#!/usr/bin/env python3
"""
Intelligent Task Planner for MCP Orchestrator
Analyzes available tools and creates optimal, compliant task plans
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TaskStep:
    """Represents a single step in a task plan."""
    step_number: int
    server_name: str
    tool_name: str
    description: str
    arguments: Dict[str, Any]
    expected_duration: str
    risk_level: RiskLevel
    dependencies: List[int] = field(default_factory=list)
    parallel_execution: bool = False
    validation_required: bool = False
    rollback_step: Optional[int] = None
    compliance_checks: List[str] = field(default_factory=list)

@dataclass
class TaskPlan:
    """Represents a complete task execution plan."""
    plan_id: str
    task_description: str
    priority: TaskPriority
    total_steps: int
    estimated_duration: str
    overall_risk: RiskLevel
    steps: List[TaskStep]
    compliance_requirements: List[str]
    approval_required: bool
    rollback_strategy: str
    success_criteria: List[str]
    failure_handling: str

class IntelligentTaskPlanner:
    """
    Intelligent task planner that analyzes available tools and creates
    optimal, compliant, and enterprise-grade execution plans.
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.deployment_patterns = self._load_deployment_patterns()
        self.risk_matrix = self._load_risk_matrix()
        self.compliance_rules = self._load_compliance_rules()
    
    def _load_deployment_patterns(self) -> Dict[str, List[str]]:
        """Load common deployment patterns and best practices."""
        return {
            "production_deployment": [
                "build",
                "test",
                "quality_scan",
                "security_scan",
                "staging_deploy",
                "staging_validation",
                "production_deploy_canary",
                "production_monitoring",
                "production_scale",
                "notification"
            ],
            "staging_deployment": [
                "build",
                "test",
                "quality_scan",
                "staging_deploy",
                "validation",
                "notification"
            ],
            "hotfix_deployment": [
                "build",
                "critical_tests",
                "production_deploy_blue_green",
                "immediate_validation",
                "monitoring",
                "notification"
            ],
            "rollback": [
                "backup_verification",
                "traffic_drain",
                "deployment_rollback",
                "validation",
                "traffic_restore",
                "notification"
            ]
        }
    
    def _load_risk_matrix(self) -> Dict[str, RiskLevel]:
        """Load risk levels for different operations."""
        return {
            "view": RiskLevel.LOW,
            "read": RiskLevel.LOW,
            "list": RiskLevel.LOW,
            "get": RiskLevel.LOW,
            "create": RiskLevel.MEDIUM,
            "build": RiskLevel.MEDIUM,
            "test": RiskLevel.MEDIUM,
            "scan": RiskLevel.MEDIUM,
            "deploy": RiskLevel.HIGH,
            "scale": RiskLevel.HIGH,
            "update": RiskLevel.HIGH,
            "delete": RiskLevel.CRITICAL,
            "drop": RiskLevel.CRITICAL,
            "remove": RiskLevel.CRITICAL,
            "destroy": RiskLevel.CRITICAL
        }
    
    def _load_compliance_rules(self) -> Dict[str, List[str]]:
        """Load compliance requirements for different environments."""
        return {
            "production": [
                "quality_gate_passed",
                "security_scan_passed",
                "approval_required",
                "backup_verified",
                "rollback_plan_ready",
                "monitoring_enabled"
            ],
            "staging": [
                "quality_gate_passed",
                "tests_passed"
            ],
            "development": [
                "tests_passed"
            ]
        }
    
    def analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user input to understand intent and extract parameters.
        
        Args:
            user_input: Natural language command from user
            
        Returns:
            Intent analysis with parameters
        """
        user_input_lower = user_input.lower()
        
        intent = {
            "action": None,
            "target": None,
            "environment": "production",  # default
            "urgency": "normal",
            "parameters": {}
        }
        
        # Detect action
        if any(word in user_input_lower for word in ["deploy", "deployment", "release"]):
            intent["action"] = "deploy"
        elif any(word in user_input_lower for word in ["rollback", "revert"]):
            intent["action"] = "rollback"
        elif any(word in user_input_lower for word in ["scale", "scaling"]):
            intent["action"] = "scale"
        elif any(word in user_input_lower for word in ["build"]):
            intent["action"] = "build"
        elif any(word in user_input_lower for word in ["test"]):
            intent["action"] = "test"
        
        # Detect environment
        if any(word in user_input_lower for word in ["prod", "production"]):
            intent["environment"] = "production"
        elif any(word in user_input_lower for word in ["staging", "stage"]):
            intent["environment"] = "staging"
        elif any(word in user_input_lower for word in ["dev", "development"]):
            intent["environment"] = "development"
        
        # Detect urgency
        if any(word in user_input_lower for word in ["urgent", "emergency", "hotfix", "critical", "now", "asap"]):
            intent["urgency"] = "urgent"
        elif any(word in user_input_lower for word in ["fast", "quick"]):
            intent["urgency"] = "fast"
        
        # Extract target (try to find microservice name, app name, etc.)
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ["code", "app", "application", "service", "microservice"]:
                if i + 1 < len(words):
                    intent["target"] = words[i + 1]
                break
        
        return intent
    
    def get_available_capabilities(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all available tools from all running servers.
        
        Returns:
            Dictionary mapping server names to their available tools
        """
        capabilities = {}
        
        for server_name, server in self.orchestrator.servers.items():
            if server.status == "running":
                if server_name not in self.orchestrator.server_capabilities:
                    self.orchestrator.discover_server_capabilities(server_name)
                
                server_caps = self.orchestrator.server_capabilities.get(server_name, {})
                capabilities[server_name] = server_caps.get("tools", [])
        
        return capabilities
    
    def find_tools_for_action(self, action: str, capabilities: Dict[str, List[Dict[str, Any]]]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Find tools that match a specific action across all servers.
        
        Args:
            action: Action keyword to search for
            capabilities: Available capabilities from all servers
            
        Returns:
            List of (server_name, tool) tuples
        """
        matching_tools = []
        
        for server_name, tools in capabilities.items():
            for tool in tools:
                tool_name = tool.get("name", "").lower()
                tool_desc = tool.get("description", "").lower()
                
                if action in tool_name or action in tool_desc:
                    matching_tools.append((server_name, tool))
        
        return matching_tools
    
    def assess_tool_risk(self, tool_name: str, environment: str) -> RiskLevel:
        """
        Assess the risk level of using a tool in a specific environment.
        
        Args:
            tool_name: Name of the tool
            environment: Target environment
            
        Returns:
            Risk level
        """
        tool_lower = tool_name.lower()
        
        # Check risk matrix
        for keyword, risk in self.risk_matrix.items():
            if keyword in tool_lower:
                # Increase risk for production
                if environment == "production":
                    if risk == RiskLevel.MEDIUM:
                        return RiskLevel.HIGH
                    elif risk == RiskLevel.HIGH:
                        return RiskLevel.CRITICAL
                return risk
        
        # Default risk
        return RiskLevel.MEDIUM if environment == "production" else RiskLevel.LOW
    
    def create_deployment_plan(self, intent: Dict[str, Any], capabilities: Dict[str, List[Dict[str, Any]]]) -> TaskPlan:
        """
        Create an intelligent deployment plan based on intent and available tools.
        
        Args:
            intent: Analyzed user intent
            capabilities: Available capabilities
            
        Returns:
            Complete task plan
        """
        environment = intent["environment"]
        urgency = intent["urgency"]
        target = intent.get("target", "application")
        
        steps = []
        step_num = 1
        
        # Determine deployment pattern
        if urgency == "urgent":
            pattern = self.deployment_patterns["hotfix_deployment"]
        elif environment == "production":
            pattern = self.deployment_patterns["production_deployment"]
        elif environment == "staging":
            pattern = self.deployment_patterns["staging_deployment"]
        else:
            pattern = ["build", "test", "deploy"]
        
        # Map pattern steps to available tools
        for pattern_step in pattern:
            matching_tools = self.find_tools_for_action(pattern_step, capabilities)
            
            if matching_tools:
                server_name, tool = matching_tools[0]  # Use first match
                tool_name = tool.get("name", "unknown")
                tool_desc = tool.get("description", f"{pattern_step} operation")
                
                risk = self.assess_tool_risk(tool_name, environment)
                
                # Build arguments based on tool schema
                arguments = self._build_tool_arguments(tool, intent)
                
                step = TaskStep(
                    step_number=step_num,
                    server_name=server_name,
                    tool_name=tool_name,
                    description=f"{tool_desc} for {target}",
                    arguments=arguments,
                    expected_duration=self._estimate_duration(pattern_step),
                    risk_level=risk,
                    dependencies=[step_num - 1] if step_num > 1 else [],
                    validation_required=environment == "production" and risk.value in ["high", "critical"],
                    compliance_checks=self.compliance_rules.get(environment, [])
                )
                
                steps.append(step)
                step_num += 1
        
        # Calculate overall risk
        overall_risk = self._calculate_overall_risk(steps)
        
        # Determine if approval is required
        approval_required = environment == "production" or overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Estimate total duration
        total_duration = self._calculate_total_duration(steps)
        
        # Create the plan
        plan = TaskPlan(
            plan_id=f"plan_{intent['action']}_{environment}_{int(__import__('time').time())}",
            task_description=f"Deploy {target} to {environment}" + (" (URGENT)" if urgency == "urgent" else ""),
            priority=TaskPriority.CRITICAL if urgency == "urgent" else TaskPriority.HIGH,
            total_steps=len(steps),
            estimated_duration=total_duration,
            overall_risk=overall_risk,
            steps=steps,
            compliance_requirements=self.compliance_rules.get(environment, []),
            approval_required=approval_required,
            rollback_strategy=self._create_rollback_strategy(steps),
            success_criteria=self._define_success_criteria(intent, environment),
            failure_handling="Automatic rollback to previous stable version with immediate notification"
        )
        
        return plan
    
    def _build_tool_arguments(self, tool: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Build tool arguments based on tool schema and intent."""
        arguments = {}
        
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        # Map common parameters
        param_mapping = {
            "name": intent.get("target", "application"),
            "environment": intent["environment"],
            "version": intent.get("parameters", {}).get("version", "latest"),
            "replicas": intent.get("parameters", {}).get("replicas", 2),
            "namespace": "default"
        }
        
        for param_name in properties.keys():
            param_lower = param_name.lower()
            for key, value in param_mapping.items():
                if key in param_lower:
                    arguments[param_name] = value
                    break
        
        return arguments
    
    def _estimate_duration(self, step_type: str) -> str:
        """Estimate duration for a step type."""
        durations = {
            "build": "2-5 minutes",
            "test": "3-7 minutes",
            "quality_scan": "2-4 minutes",
            "security_scan": "3-5 minutes",
            "deploy": "2-3 minutes",
            "validation": "1-2 minutes",
            "monitoring": "5 minutes",
            "notification": "< 30 seconds"
        }
        return durations.get(step_type, "1-2 minutes")
    
    def _calculate_overall_risk(self, steps: List[TaskStep]) -> RiskLevel:
        """Calculate overall risk from all steps."""
        max_risk = RiskLevel.LOW
        
        for step in steps:
            if step.risk_level == RiskLevel.CRITICAL:
                return RiskLevel.CRITICAL
            elif step.risk_level == RiskLevel.HIGH and max_risk != RiskLevel.CRITICAL:
                max_risk = RiskLevel.HIGH
            elif step.risk_level == RiskLevel.MEDIUM and max_risk == RiskLevel.LOW:
                max_risk = RiskLevel.MEDIUM
        
        return max_risk
    
    def _calculate_total_duration(self, steps: List[TaskStep]) -> str:
        """Calculate total estimated duration."""
        # Simplified: assume sequential execution
        # In reality, some steps can be parallel
        min_total = sum(int(step.expected_duration.split('-')[0].split()[0]) for step in steps)
        return f"{min_total}-{min_total + len(steps) * 2} minutes"
    
    def _create_rollback_strategy(self, steps: List[TaskStep]) -> str:
        """Create a rollback strategy for the plan."""
        high_risk_steps = [s for s in steps if s.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        
        if high_risk_steps:
            return f"Automatic rollback available for {len(high_risk_steps)} critical steps. Previous version maintained as backup. Blue-green deployment ensures zero-downtime rollback."
        else:
            return "Standard rollback available. Can revert to previous state with minimal impact."
    
    def _define_success_criteria(self, intent: Dict[str, Any], environment: str) -> List[str]:
        """Define success criteria for the task."""
        criteria = [
            "All steps completed without errors",
            "Health checks passed",
            "No error logs in monitoring"
        ]
        
        if environment == "production":
            criteria.extend([
                "Zero user-facing errors",
                "Response time within SLA",
                "All pods running and ready",
                "Traffic routing correctly"
            ])
        
        return criteria
    
    def format_plan_for_display(self, plan: TaskPlan) -> str:
        """
        Format the task plan for human-readable display.
        
        Args:
            plan: Task plan to format
            
        Returns:
            Formatted string representation
        """
        output = []
        output.append("=" * 80)
        output.append(f"📋 INTELLIGENT TASK PLAN: {plan.plan_id}")
        output.append("=" * 80)
        output.append(f"\n🎯 Task: {plan.task_description}")
        output.append(f"⚡ Priority: {plan.priority.value.upper()}")
        output.append(f"⚠️  Overall Risk: {plan.overall_risk.value.upper()}")
        output.append(f"⏱️  Estimated Duration: {plan.estimated_duration}")
        output.append(f"📊 Total Steps: {plan.total_steps}")
        
        if plan.approval_required:
            output.append(f"\n⚠️  APPROVAL REQUIRED - High-risk operation in production environment")
        
        output.append(f"\n📜 Compliance Requirements:")
        for req in plan.compliance_requirements:
            output.append(f"  ✓ {req}")
        
        output.append(f"\n🔄 Rollback Strategy:")
        output.append(f"  {plan.rollback_strategy}")
        
        output.append(f"\n✅ Success Criteria:")
        for criteria in plan.success_criteria:
            output.append(f"  • {criteria}")
        
        output.append(f"\n🚨 Failure Handling:")
        output.append(f"  {plan.failure_handling}")
        
        output.append(f"\n" + "=" * 80)
        output.append("EXECUTION STEPS")
        output.append("=" * 80)
        
        for step in plan.steps:
            output.append(f"\n📍 Step {step.step_number}: {step.description}")
            output.append(f"   Server: {step.server_name}")
            output.append(f"   Tool: {step.tool_name}")
            output.append(f"   Risk: {step.risk_level.value.upper()} {self._get_risk_emoji(step.risk_level)}")
            output.append(f"   Duration: {step.expected_duration}")
            
            if step.dependencies:
                output.append(f"   Dependencies: Steps {', '.join(map(str, step.dependencies))}")
            
            if step.arguments:
                output.append(f"   Arguments:")
                for key, value in step.arguments.items():
                    output.append(f"     • {key}: {value}")
            
            if step.validation_required:
                output.append(f"   ⚠️  Manual validation required after this step")
            
            if step.compliance_checks:
                output.append(f"   Compliance: {', '.join(step.compliance_checks)}")
        
        output.append(f"\n" + "=" * 80)
        output.append("Would you like to proceed with this plan? (yes/no)")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def _get_risk_emoji(self, risk: RiskLevel) -> str:
        """Get emoji for risk level."""
        emoji_map = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴"
        }
        return emoji_map.get(risk, "⚪")
    
    def create_plan_from_user_input(self, user_input: str) -> str:
        """
        Main entry point: Create a complete task plan from user input.
        
        Args:
            user_input: Natural language command from user
            
        Returns:
            Formatted task plan ready for presentation
        """
        # Step 1: Analyze user intent
        intent = self.analyze_user_intent(user_input)
        
        if not intent["action"]:
            return "❌ Unable to understand the requested action. Please specify what you'd like to do (e.g., deploy, rollback, scale)"
        
        # Step 2: Get available capabilities
        capabilities = self.get_available_capabilities()
        
        if not capabilities:
            return "❌ No MCP servers are currently running. Please start servers first using 'start_all_enabled_servers'"
        
        # Step 3: Create the plan
        plan = self.create_deployment_plan(intent, capabilities)
        
        # Step 4: Format for display
        return self.format_plan_for_display(plan)
