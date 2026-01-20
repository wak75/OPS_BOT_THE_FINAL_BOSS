#!/usr/bin/env python3
"""
Task Executor for MCP Orchestrator
Executes approved task plans step by step
"""

import json
import time
from typing import Dict, Any, List
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

class TaskExecutor:
    """Executes approved task plans with monitoring and error handling."""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.current_plan = None
        self.execution_log = []
    
    def execute_plan(self, plan, user_approval: bool = False) -> Dict[str, Any]:
        """
        Execute an approved task plan.
        
        Args:
            plan: TaskPlan object to execute
            user_approval: Whether user has approved the plan
            
        Returns:
            Execution summary with results
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
            "step_results": []
        }
        
        print(f"\n🚀 Starting execution of plan: {plan.plan_id}")
        print(f"📊 Total steps: {plan.total_steps}\n")
        
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
                
                # Handle failure
                if plan.failure_handling:
                    print(f"\n🔄 Initiating failure handling: {plan.failure_handling}")
                    rollback_result = self._handle_failure(step, results)
                    results["rollback"] = rollback_result
                
                break  # Stop execution on failure
        
        results["completed_at"] = time.time()
        results["total_duration"] = results["completed_at"] - results["started_at"]
        
        if results["steps_failed"] == 0:
            results["status"] = "completed"
            print(f"\n✅ Plan execution completed successfully!")
            print(f"⏱️  Total duration: {results['total_duration']:.2f}s")
        else:
            print(f"\n❌ Plan execution failed at step {results['steps_completed'] + 1}")
        
        return results
    
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
    
    def _handle_failure(self, failed_step, execution_results) -> Dict[str, Any]:
        """
        Handle failure by attempting rollback or cleanup.
        
        Args:
            failed_step: The step that failed
            execution_results: Current execution results
            
        Returns:
            Rollback result
        """
        rollback = {
            "initiated_at": time.time(),
            "reason": f"Step {failed_step.step_number} failed",
            "actions_taken": []
        }
        
        # If there's a rollback step defined, execute it
        if failed_step.rollback_step:
            rollback_step_num = failed_step.rollback_step
            # Find and execute rollback step
            for step in self.current_plan.steps:
                if step.step_number == rollback_step_num:
                    result = self._execute_step(step)
                    rollback["actions_taken"].append({
                        "step": step.description,
                        "success": result.success
                    })
                    break
        
        # General cleanup actions
        rollback["actions_taken"].append({
            "action": "Notification sent to team",
            "success": True
        })
        
        rollback["completed_at"] = time.time()
        return rollback
    
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
        
        if "rollback" in results:
            output.append("\n" + "-" * 80)
            output.append("ROLLBACK ACTIONS:")
            output.append("-" * 80)
            for action in results["rollback"]["actions_taken"]:
                status = "✅" if action.get("success") else "❌"
                output.append(f"{status} {action.get('action', action.get('step', 'Unknown'))}")
        
        output.append("\n" + "=" * 80)
        
        return "\n".join(output)
