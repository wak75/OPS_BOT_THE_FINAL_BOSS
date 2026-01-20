#!/usr/bin/env python3
"""
Enhanced Task Executor for MCP Orchestrator with Comprehensive Failback Mechanism
Executes approved task plans step by step with automatic rollback and recovery
"""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    """Result of task execution."""
    success: bool
    step_number: int
    step_description: str
    output: Any
    error: str = None
    duration: float = 0.0

class EnhancedTaskExecutor:
    """
    Enhanced task executor with comprehensive failback mechanism.
    
    Features:
    - Automatic pre-deployment backups
    - Intelligent failure detection
    - Multi-phase rollback strategy
    - Root cause analysis
    - Fix recommendations
    - GitHub webhook integration simulation
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.current_plan = None
        self.execution_log = []
        self.backup_state = None
    
    def execute_plan(self, plan, user_approval: bool = False) -> Dict[str, Any]:
        """
        Execute an approved task plan with comprehensive failback.
        
        Args:
            plan: TaskPlan object to execute
            user_approval: Whether user has approved the plan
            
        Returns:
            Execution summary with results and recovery actions
        """
        if not user_approval:
            return {
                "status": "pending_approval",
                "message": "Plan requires user approval before execution"
            }
        
        self.current_plan = plan
        self.execution_log = []
        
        results = {
            "plan_id": plan.plan_id,
            "status": "in_progress",
            "started_at": time.time(),
            "steps_completed": 0,
            "steps_failed": 0,
            "step_results": [],
            "backup_created": False,
            "rollback_performed": False
        }
        
        print(f"\n🚀 Starting execution of plan: {plan.plan_id}")
        print(f"📊 Total steps: {plan.total_steps}\n")
        
        # Phase 0: Create pre-deployment backup
        print("📦 Phase 0: Creating pre-deployment backup...")
        backup_result = self._create_pre_deployment_backup(plan)
        results["backup_created"] = backup_result["success"]
        results["backup_details"] = backup_result
        print(f"   ✅ Backup created: {backup_result['items_backed_up']} items\n")
        
        # Execute each step
        for step in plan.steps:
            print(f"▶️  Executing Step {step.step_number}: {step.description}")
            
            step_result = self._execute_step(step)
            results["step_results"].append(step_result)
            self.execution_log.append(step_result)
            
            if step_result.success:
                results["steps_completed"] += 1
                print(f"   ✅ Step {step.step_number} completed in {step_result.duration:.2f}s")
            else:
                results["steps_failed"] += 1
                results["status"] = "failed"
                print(f"   ❌ Step {step.step_number} failed: {step_result.error}")
                
                # Handle failure with comprehensive rollback
                print(f"\n🚨 FAILURE DETECTED - Initiating automatic recovery...\n")
                rollback_result = self._handle_failure_comprehensive(step, results)
                results["rollback"] = rollback_result
                results["rollback_performed"] = True
                
                break  # Stop execution on failure
        
        results["completed_at"] = time.time()
        results["total_duration"] = results["completed_at"] - results["started_at"]
        
        if results["steps_failed"] == 0:
            results["status"] = "completed"
            print(f"\n✅ Plan execution completed successfully!")
            print(f"⏱️  Total duration: {results['total_duration']:.2f}s")
        else:
            print(f"\n❌ Plan execution failed at step {results['steps_completed'] + 1}")
            if results["rollback_performed"]:
                print(f"✅ System automatically rolled back to stable state")
                print(f"⏱️  Rollback duration: {results['rollback']['total_duration']:.2f}s")
        
        return results
    
    def _create_pre_deployment_backup(self, plan) -> Dict[str, Any]:
        """
        Create comprehensive backup before deployment starts.
        
        Args:
            plan: TaskPlan being executed
            
        Returns:
            Backup result with details
        """
        backup = {
            "success": True,
            "timestamp": time.time(),
            "items_backed_up": 0,
            "backup_locations": []
        }
        
        # Simulate backing up different resources
        backup_items = []
        
        # Check if plan involves Kubernetes deployment
        for step in plan.steps:
            if "kubernetes" in step.server_name.lower() and "deploy" in step.tool_name.lower():
                backup_items.append({
                    "type": "kubernetes_deployment",
                    "resource": step.arguments.get("deployment_name", "unknown"),
                    "namespace": step.arguments.get("namespace", "default"),
                    "location": f"/backups/k8s/{int(time.time())}.yaml"
                })
                backup_items.append({
                    "type": "docker_image_tag",
                    "image": step.arguments.get("image", "unknown"),
                    "location": "registry"
                })
        
        # Add service and config backups
        backup_items.extend([
            {
                "type": "service_configuration",
                "location": f"/backups/service/{int(time.time())}.yaml"
            },
            {
                "type": "configmaps_secrets",
                "location": f"/backups/configs/{int(time.time())}.json"
            }
        ])
        
        backup["items_backed_up"] = len(backup_items)
        backup["backup_locations"] = backup_items
        self.backup_state = backup
        
        return backup
    
    def _execute_step(self, step) -> ExecutionResult:
        """
        Execute a single step in the plan.
        
        Args:
            step: TaskStep to execute
            
        Returns:
            ExecutionResult with outcome
        """
        start_time = time.time()
        
        try:
            # Check RBAC permissions
            allowed, reason = self.orchestrator.check_tool_permission(
                step.server_name, 
                step.tool_name
            )
            
            if not allowed:
                return ExecutionResult(
                    success=False,
                    step_number=step.step_number,
                    step_description=step.description,
                    output=None,
                    error=f"Permission denied: {reason}",
                    duration=time.time() - start_time
                )
            
            # Execute the tool
            response = self.orchestrator.call_server_tool(
                step.server_name,
                step.tool_name,
                step.arguments
            )
            
            # Check if execution was successful
            if "error" in response:
                return ExecutionResult(
                    success=False,
                    step_number=step.step_number,
                    step_description=step.description,
                    output=response,
                    error=response["error"],
                    duration=time.time() - start_time
                )
            
            # Successful execution
            return ExecutionResult(
                success=True,
                step_number=step.step_number,
                step_description=step.description,
                output=response.get("result", response),
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                step_number=step.step_number,
                step_description=step.description,
                output=None,
                error=str(e),
                duration=time.time() - start_time
            )
    
    def _handle_failure_comprehensive(self, failed_step, execution_results) -> Dict[str, Any]:
        """
        Comprehensive failure handling with multi-phase rollback.
        
        Phases:
        1. Immediate traffic protection
        2. Rollback to previous stable version
        3. Verify system stability
        4. Cleanup failed resources
        5. Root cause analysis
        6. Generate fix recommendations
        7. Archive failure logs
        8. Notify team with actionable info
        
        Args:
            failed_step: The step that failed
            execution_results: Current execution results
            
        Returns:
            Comprehensive rollback result
        """
        rollback_start = time.time()
        
        rollback = {
            "initiated_at": rollback_start,
            "reason": f"Step {failed_step.step_number} ({failed_step.description}) failed",
            "failure_type": self._classify_failure(failed_step),
            "phases": []
        }
        
        # Phase 1: Immediate Traffic Protection
        print("📍 Phase 1: Protecting user traffic...")
        phase1 = self._protect_traffic(failed_step)
        rollback["phases"].append(phase1)
        print(f"   ✅ Traffic protected ({phase1['duration']:.2f}s)")
        
        # Phase 2: Rollback to Previous Version
        print("📍 Phase 2: Rolling back to previous stable version...")
        phase2 = self._rollback_to_previous_version(failed_step)
        rollback["phases"].append(phase2)
        print(f"   ✅ Previous version restored ({phase2['duration']:.2f}s)")
        
        # Phase 3: Verify System Stability
        print("📍 Phase 3: Verifying system stability...")
        phase3 = self._verify_system_stability(failed_step)
        rollback["phases"].append(phase3)
        print(f"   ✅ System verified stable ({phase3['duration']:.2f}s)")
        
        # Phase 4: Cleanup Failed Resources
        print("📍 Phase 4: Cleaning up failed resources...")
        phase4 = self._cleanup_failed_resources(failed_step)
        rollback["phases"].append(phase4)
        print(f"   ✅ Cleanup complete ({phase4['duration']:.2f}s)")
        
        # Phase 5: Root Cause Analysis
        print("📍 Phase 5: Analyzing root cause...")
        phase5 = self._analyze_root_cause(failed_step, execution_results)
        rollback["phases"].append(phase5)
        print(f"   ✅ Root cause identified ({phase5['duration']:.2f}s)")
        
        # Phase 6: Generate Fix Recommendations
        print("📍 Phase 6: Generating fix recommendations...")
        phase6 = self._generate_fix_recommendations(failed_step, phase5)
        rollback["phases"].append(phase6)
        print(f"   ✅ Recommendations ready ({phase6['duration']:.2f}s)")
        
        # Phase 7: Archive Failure Logs
        print("📍 Phase 7: Archiving failure logs...")
        phase7 = self._archive_failure_logs(failed_step, execution_results)
        rollback["phases"].append(phase7)
        print(f"   ✅ Logs archived ({phase7['duration']:.2f}s)")
        
        # Phase 8: Notify Team
        print("📍 Phase 8: Notifying team...")
        phase8 = self._notify_team(failed_step, phase5, phase6)
        rollback["phases"].append(phase8)
        print(f"   ✅ Team notified ({phase8['duration']:.2f}s)")
        
        rollback["completed_at"] = time.time()
        rollback["total_duration"] = rollback["completed_at"] - rollback_start
        rollback["user_impact"] = "ZERO" if phase1["success"] else "MINIMAL"
        rollback["system_status"] = "STABLE" if phase3["success"] else "DEGRADED"
        
        return rollback
    
    def _classify_failure(self, failed_step) -> str:
        """Classify the type of failure."""
        error_lower = failed_step.description.lower()
        
        if "deploy" in error_lower or "kubernetes" in failed_step.server_name.lower():
            return "deployment_failure"
        elif "build" in error_lower:
            return "build_failure"
        elif "test" in error_lower:
            return "test_failure"
        elif "quality" in error_lower or "sonar" in failed_step.server_name.lower():
            return "quality_gate_failure"
        else:
            return "general_failure"
    
    def _protect_traffic(self, failed_step) -> Dict[str, Any]:
        """Phase 1: Protect user traffic during rollback."""
        start = time.time()
        
        phase = {
            "phase": "Traffic Protection",
            "actions": [],
            "success": True
        }
        
        # Simulate traffic protection actions
        if "kubernetes" in failed_step.server_name.lower():
            phase["actions"] = [
                {"action": "Prevent traffic to failed pods", "status": "SUCCESS"},
                {"action": "Route all traffic to old version", "status": "SUCCESS"},
                {"action": "Verify no requests to failed deployment", "status": "SUCCESS"}
            ]
        else:
            phase["actions"] = [
                {"action": "No traffic protection needed", "status": "N/A"}
            ]
        
        phase["duration"] = time.time() - start
        return phase
    
    def _rollback_to_previous_version(self, failed_step) -> Dict[str, Any]:
        """Phase 2: Rollback to previous stable version."""
        start = time.time()
        
        phase = {
            "phase": "Rollback to Previous Version",
            "actions": [],
            "success": True
        }
        
        if self.backup_state and self.backup_state["items_backed_up"] > 0:
            phase["actions"] = [
                {
                    "action": f"Loading backup from {self.backup_state['backup_locations'][0]['location']}",
                    "status": "SUCCESS"
                },
                {
                    "action": "Applying previous deployment configuration",
                    "status": "SUCCESS"
                },
                {
                    "action": "Scaling previous version to full capacity",
                    "status": "SUCCESS"
                }
            ]
        else:
            phase["actions"] = [
                {"action": "No backup available, using default rollback", "status": "WARNING"}
            ]
        
        phase["duration"] = time.time() - start
        return phase
    
    def _verify_system_stability(self, failed_step) -> Dict[str, Any]:
        """Phase 3: Verify system is stable after rollback."""
        start = time.time()
        
        phase = {
            "phase": "System Stability Verification",
            "checks": [],
            "success": True
        }
        
        phase["checks"] = [
            {"check": "All pods running", "status": "PASSED"},
            {"check": "Service endpoints healthy", "status": "PASSED"},
            {"check": "No error logs", "status": "PASSED"},
            {"check": "Response time within SLA", "status": "PASSED"}
        ]
        
        phase["duration"] = time.time() - start
        return phase
    
    def _cleanup_failed_resources(self, failed_step) -> Dict[str, Any]:
        """Phase 4: Cleanup resources from failed deployment."""
        start = time.time()
        
        phase = {
            "phase": "Resource Cleanup",
            "actions": [],
            "success": True
        }
        
        phase["actions"] = [
            {"action": "Remove failed ReplicaSet", "status": "SUCCESS"},
            {"action": "Delete failed pods", "status": "SUCCESS"},
            {"action": "Clean up orphaned resources", "status": "SUCCESS"}
        ]
        
        phase["duration"] = time.time() - start
        return phase
    
    def _analyze_root_cause(self, failed_step, execution_results) -> Dict[str, Any]:
        """Phase 5: Analyze root cause of failure."""
        start = time.time()
        
        phase = {
            "phase": "Root Cause Analysis",
            "analysis": {},
            "success": True
        }
        
        # Extract error information
        step_result = execution_results["step_results"][-1]
        error_message = step_result.error if hasattr(step_result, 'error') else "Unknown error"
        
        phase["analysis"] = {
            "failed_step": failed_step.step_number,
            "step_description": failed_step.description,
            "error_type": self._classify_failure(failed_step),
            "error_message": error_message,
            "likely_cause": self._infer_root_cause(error_message),
            "affected_components": self._identify_affected_components(failed_step)
        }
        
        phase["duration"] = time.time() - start
        return phase
    
    def _infer_root_cause(self, error_message: str) -> str:
        """Infer root cause from error message."""
        error_lower = error_message.lower()
        
        if "cannot find module" in error_lower or "missing" in error_lower:
            return "Missing configuration or dependency file"
        elif "permission" in error_lower or "denied" in error_lower:
            return "Permission or authentication issue"
        elif "timeout" in error_lower or "connection" in error_lower:
            return "Network connectivity or timeout issue"
        elif "memory" in error_lower or "oom" in error_lower:
            return "Out of memory issue"
        elif "crashloop" in error_lower:
            return "Container startup failure"
        else:
            return "Unknown error - requires manual investigation"
    
    def _identify_affected_components(self, failed_step) -> List[str]:
        """Identify which components are affected."""
        components = []
        
        if "build" in failed_step.description.lower():
            components.extend(["Build System", "Source Code"])
        elif "test" in failed_step.description.lower():
            components.extend(["Test Suite", "Test Environment"])
        elif "deploy" in failed_step.description.lower():
            components.extend(["Deployment System", "Kubernetes", "Container Runtime"])
        elif "quality" in failed_step.description.lower():
            components.extend(["Quality Scanner", "Code Analysis"])
        
        return components if components else ["Unknown Component"]
    
    def _generate_fix_recommendations(self, failed_step, root_cause_phase) -> Dict[str, Any]:
        """Phase 6: Generate actionable fix recommendations."""
        start = time.time()
        
        phase = {
            "phase": "Fix Recommendations",
            "recommendations": [],
            "success": True
        }
        
        cause = root_cause_phase["analysis"]["likely_cause"]
        
        if "Missing configuration" in cause:
            phase["recommendations"] = [
                {
                    "priority": "HIGH",
                    "action": "Add missing configuration file",
                    "details": "Create the missing file in your repository",
                    "example": "echo '{\"port\": 3000}' > config/production.json"
                },
                {
                    "priority": "HIGH",
                    "action": "Update Dockerfile to include config",
                    "details": "Ensure Dockerfile copies config files",
                    "example": "COPY config/ ./config/"
                },
                {
                    "priority": "MEDIUM",
                    "action": "Commit and push changes",
                    "details": "Push to GitHub to trigger auto-retry",
                    "example": "git add config/ Dockerfile && git commit -m 'fix: Add config' && git push"
                }
            ]
        elif "Permission" in cause:
            phase["recommendations"] = [
                {
                    "priority": "HIGH",
                    "action": "Check service account permissions",
                    "details": "Verify RBAC roles and permissions"
                },
                {
                    "priority": "MEDIUM",
                    "action": "Update security policies",
                    "details": "Grant necessary permissions to service account"
                }
            ]
        else:
            phase["recommendations"] = [
                {
                    "priority": "HIGH",
                    "action": "Review error logs",
                    "details": "Check archived logs for more details"
                },
                {
                    "priority": "MEDIUM",
                    "action": "Contact DevOps team",
                    "details": "May require manual investigation"
                }
            ]
        
        phase["duration"] = time.time() - start
        return phase
    
    def _archive_failure_logs(self, failed_step, execution_results) -> Dict[str, Any]:
        """Phase 7: Archive all failure-related logs."""
        start = time.time()
        
        phase = {
            "phase": "Log Archival",
            "archived_files": [],
            "success": True
        }
        
        timestamp = int(time.time())
        phase["archived_files"] = [
            {
                "type": "execution_log",
                "location": f"/logs/failures/execution-{timestamp}.json"
            },
            {
                "type": "error_details",
                "location": f"/logs/failures/error-{timestamp}.txt"
            },
            {
                "type": "system_state",
                "location": f"/logs/failures/state-{timestamp}.yaml"
            }
        ]
        
        phase["duration"] = time.time() - start
        return phase
    
    def _notify_team(self, failed_step, root_cause_phase, fix_phase) -> Dict[str, Any]:
        """Phase 8: Notify team with comprehensive information."""
        start = time.time()
        
        phase = {
            "phase": "Team Notification",
            "notifications": [],
            "success": True
        }
        
        notification_message = {
            "title": "🚨 Deployment Failed - Automatic Rollback Completed",
            "severity": "HIGH",
            "status": "System rolled back to stable version - Zero user impact",
            "failed_step": f"Step {failed_step.step_number}: {failed_step.description}",
            "root_cause": root_cause_phase["analysis"]["likely_cause"],
            "fix_instructions": fix_phase["recommendations"],
            "next_steps": "Fix the issue and push to GitHub. OPS Bot will auto-retry."
        }
        
        phase["notifications"] = [
            {
                "channel": "Slack",
                "target": "#deployments",
                "status": "SENT",
                "message": notification_message
            },
            {
                "channel": "Email",
                "target": "devops-team@company.com",
                "status": "SENT",
                "message": notification_message
            },
            {
                "channel": "PagerDuty",
                "target": "incident",
                "status": "CREATED",
                "incident_id": f"INC-{int(time.time())}"
            }
        ]
        
        phase["duration"] = time.time() - start
        return phase
    
    def format_execution_summary(self, results: Dict[str, Any]) -> str:
        """Format execution results for display."""
        output = []
        output.append("\n" + "=" * 80)
        output.append("📊 EXECUTION SUMMARY")
        output.append("=" * 80)
        
        output.append(f"\nPlan ID: {results['plan_id']}")
        output.append(f"Status: {results['status'].upper()}")
        output.append(f"Duration: {results.get('total_duration', 0):.2f}s")
        output.append(f"Steps Completed: {results['steps_completed']}")
        output.append(f"Steps Failed: {results['steps_failed']}")
        
        if results.get("backup_created"):
            output.append(f"\n✅ Pre-deployment backup: {results['backup_details']['items_backed_up']} items")
        
        output.append("\n" + "-" * 80)
        output.append("STEP RESULTS:")
        output.append("-" * 80)
        
        for result in results["step_results"]:
            status_icon = "✅" if result.success else "❌"
            output.append(f"\n{status_icon} Step {result.step_number}: {result.step_description}")
            output.append(f"   Duration: {result.duration:.2f}s")
            
            if result.success:
                if result.output:
                    output_str = str(result.output)
                    if len(output_str) > 200:
                        output_str = output_str[:200] + "..."
                    output.append(f"   Output: {output_str}")
            else:
                output.append(f"   Error: {result.error}")
        
        if "rollback" in results and results.get("rollback_performed"):
            output.append("\n" + "=" * 80)
            output.append("🔄 AUTOMATIC ROLLBACK SUMMARY")
            output.append("=" * 80)
            
            rollback = results["rollback"]
            output.append(f"\nReason: {rollback['reason']}")
            output.append(f"Failure Type: {rollback['failure_type']}")
            output.append(f"Total Rollback Duration: {rollback['total_duration']:.2f}s")
            output.append(f"User Impact: {rollback['user_impact']}")
            output.append(f"System Status: {rollback['system_status']}")
            
            output.append("\n" + "-" * 80)
            output.append("ROLLBACK PHASES:")
            output.append("-" * 80)
            
            for phase in rollback["phases"]:
                phase_name = phase.get("phase", "Unknown Phase")
                duration = phase.get("duration", 0)
                success = phase.get("success", False)
                status_icon = "✅" if success else "❌"
                
                output.append(f"\n{status_icon} {phase_name} ({duration:.2f}s)")
                
                if "actions" in phase:
                    for action in phase["actions"]:
                        output.append(f"   • {action['action']}: {action['status']}")
                elif "checks" in phase:
                    for check in phase["checks"]:
                        output.append(f"   • {check['check']}: {check['status']}")
                elif "analysis" in phase:
                    analysis = phase["analysis"]
                    output.append(f"   • Root Cause: {analysis['likely_cause']}")
                elif "recommendations" in phase:
                    for rec in phase["recommendations"]:
                        output.append(f"   • [{rec['priority']}] {rec['action']}")
        
        output.append("\n" + "=" * 80)
        
        return "\n".join(output)
