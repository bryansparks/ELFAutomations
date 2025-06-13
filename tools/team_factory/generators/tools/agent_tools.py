"""
Agent-specific tool generator based on role requirements.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

from ...models import TeamMember, TeamSpecification


class AgentToolGenerator:
    """Generates role-specific tools for agents."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Tool templates for different capabilities
        self.tool_templates = {
            "project_management": self._get_project_management_tools,
            "code_analysis": self._get_code_analysis_tools,
            "communication": self._get_communication_tools,
            "data_analysis": self._get_data_analysis_tools,
            "research": self._get_research_tools,
            "content_creation": self._get_content_creation_tools,
            "monitoring": self._get_monitoring_tools,
            "financial": self._get_financial_tools,
        }
    
    def generate_tools(self, spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate tools for all agents in the team.
        
        Returns:
            Dict with results including generated files
        """
        results = {
            "success": True,
            "generated_files": [],
            "errors": []
        }
        
        # Create tools directory
        tools_dir = Path(spec.name) / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate __init__.py
        init_content = self._generate_tools_init(spec)
        with open(tools_dir / "__init__.py", "w") as f:
            f.write(init_content)
        results["generated_files"].append("tools/__init__.py")
        
        # Generate shared tools module
        shared_tools = self._generate_shared_tools(spec)
        with open(tools_dir / "shared_tools.py", "w") as f:
            f.write(shared_tools)
        results["generated_files"].append("tools/shared_tools.py")
        
        # Generate role-specific tools
        all_tools = set()
        for member in spec.members:
            if hasattr(member, 'tools') and member.tools:
                member_tools = self._generate_member_tools(member, spec)
                if member_tools:
                    filename = f"{member.name}_tools.py"
                    with open(tools_dir / filename, "w") as f:
                        f.write(member_tools)
                    results["generated_files"].append(f"tools/{filename}")
                    all_tools.update(member.tools)
        
        # Generate team tools registry
        registry = self._generate_tools_registry(all_tools, spec)
        with open(tools_dir / "registry.py", "w") as f:
            f.write(registry)
        results["generated_files"].append("tools/registry.py")
        
        return results
    
    def _generate_tools_init(self, spec: TeamSpecification) -> str:
        """Generate __init__.py for tools module."""
        return f'''"""
Tools for {spec.name}

This module contains all tools available to agents in the team.
"""

from .shared_tools import *
from .registry import get_tools_for_agent

__all__ = ["get_tools_for_agent"]
'''
    
    def _generate_shared_tools(self, spec: TeamSpecification) -> str:
        """Generate tools shared by all team members."""
        return f'''"""
Shared tools available to all team members.
"""

from typing import Any, Dict, List, Optional
from langchain.tools import tool
import logging

logger = logging.getLogger(__name__)


@tool
def team_communication(message: str, recipient: str = "all") -> str:
    """
    Send a message to team members.
    
    Args:
        message: The message to send
        recipient: Target recipient ("all" for broadcast)
    
    Returns:
        Confirmation of message sent
    """
    logger.info(f"Team communication to {{recipient}}: {{message}}")
    return f"Message sent to {{recipient}}: {{message}}"


@tool
def log_decision(decision: str, rationale: str, impact: str = "medium") -> str:
    """
    Log an important decision for team records.
    
    Args:
        decision: The decision made
        rationale: Why this decision was made
        impact: Impact level (low/medium/high)
    
    Returns:
        Confirmation of logged decision
    """
    logger.info(f"Decision logged: {{decision}} (Impact: {{impact}})")
    return f"Decision logged: {{decision}}"


@tool
def request_clarification(topic: str, from_whom: str) -> str:
    """
    Request clarification on a topic from a team member.
    
    Args:
        topic: What needs clarification
        from_whom: Who to ask for clarification
    
    Returns:
        Clarification request status
    """
    return f"Clarification requested from {{from_whom}} about: {{topic}}"
'''
    
    def _generate_member_tools(self, member: TeamMember, spec: TeamSpecification) -> str:
        """Generate role-specific tools for a team member."""
        tools_code = f'''"""
Role-specific tools for {member.role}.
"""

from typing import Any, Dict, List, Optional
from langchain.tools import tool
import logging

logger = logging.getLogger(__name__)

'''
        
        # Add tools based on the member's required tools
        tools_added = []
        for tool_category in member.tools:
            if tool_category in self.tool_templates:
                tool_code = self.tool_templates[tool_category](member, spec)
                if tool_code:
                    tools_code += tool_code + "\n\n"
                    tools_added.append(tool_category)
        
        # If no specific tools matched, add generic capability tools
        if not tools_added:
            tools_code += self._get_generic_tools(member)
        
        return tools_code
    
    def _get_project_management_tools(self, member: TeamMember, spec: TeamSpecification) -> str:
        """Generate project management tools."""
        return '''
@tool
def create_project(name: str, description: str, priority: str = "medium") -> Dict[str, Any]:
    """
    Create a new project in the project management system.
    
    Args:
        name: Project name
        description: Project description
        priority: Priority level (low/medium/high/critical)
    
    Returns:
        Project creation result
    """
    # In production, this would use the project management MCP
    return {
        "project_id": f"proj_{name.lower().replace(' ', '_')}",
        "status": "created",
        "message": f"Project '{name}' created successfully"
    }


@tool
def assign_task(task_name: str, assignee: str, deadline: Optional[str] = None) -> str:
    """
    Assign a task to a team member.
    
    Args:
        task_name: Name of the task
        assignee: Who to assign the task to
        deadline: Optional deadline
    
    Returns:
        Task assignment confirmation
    """
    deadline_msg = f" with deadline {deadline}" if deadline else ""
    return f"Task '{task_name}' assigned to {assignee}{deadline_msg}"


@tool
def check_project_status(project_id: str) -> Dict[str, Any]:
    """
    Check the status of a project.
    
    Args:
        project_id: Project identifier
    
    Returns:
        Project status information
    """
    # Mock implementation
    return {
        "project_id": project_id,
        "status": "in_progress",
        "completion": "45%",
        "blocked_tasks": 0
    }
'''
    
    def _get_code_analysis_tools(self, member: TeamMember, spec: TeamSpecification) -> str:
        """Generate code analysis tools."""
        return '''
@tool
def analyze_code_quality(file_path: str) -> Dict[str, Any]:
    """
    Analyze code quality metrics for a file.
    
    Args:
        file_path: Path to the code file
    
    Returns:
        Code quality metrics
    """
    # Mock implementation
    return {
        "file": file_path,
        "complexity": "moderate",
        "issues": ["Consider adding type hints", "Function too long"],
        "coverage": "85%"
    }


@tool
def suggest_refactoring(code_snippet: str) -> List[str]:
    """
    Suggest refactoring improvements for code.
    
    Args:
        code_snippet: Code to analyze
    
    Returns:
        List of refactoring suggestions
    """
    return [
        "Extract method for repeated logic",
        "Use more descriptive variable names",
        "Consider using a design pattern"
    ]
'''
    
    def _get_communication_tools(self, member: TeamMember, spec: TeamSpecification) -> str:
        """Generate communication tools."""
        return '''
@tool
def schedule_meeting(topic: str, participants: List[str], duration: int = 30) -> str:
    """
    Schedule a team meeting.
    
    Args:
        topic: Meeting topic
        participants: List of participants
        duration: Meeting duration in minutes
    
    Returns:
        Meeting scheduling confirmation
    """
    participants_str = ", ".join(participants)
    return f"Meeting scheduled: '{topic}' with {participants_str} for {duration} minutes"


@tool
def send_update(update_type: str, content: str, stakeholders: List[str]) -> str:
    """
    Send an update to stakeholders.
    
    Args:
        update_type: Type of update (progress/blocker/completion)
        content: Update content
        stakeholders: List of stakeholders to notify
    
    Returns:
        Update confirmation
    """
    stakeholders_str = ", ".join(stakeholders)
    return f"{update_type.capitalize()} update sent to {stakeholders_str}"
'''
    
    def _get_data_analysis_tools(self, member: TeamMember, spec: TeamSpecification) -> str:
        """Generate data analysis tools."""
        return '''
@tool
def analyze_metrics(metric_type: str, time_period: str = "last_week") -> Dict[str, Any]:
    """
    Analyze team or project metrics.
    
    Args:
        metric_type: Type of metric to analyze
        time_period: Time period for analysis
    
    Returns:
        Metrics analysis results
    """
    # Mock implementation
    return {
        "metric_type": metric_type,
        "period": time_period,
        "trend": "improving",
        "key_insights": ["20% improvement over previous period"]
    }


@tool
def generate_report(report_type: str, data_sources: List[str]) -> str:
    """
    Generate an analytical report.
    
    Args:
        report_type: Type of report to generate
        data_sources: Data sources to include
    
    Returns:
        Report generation status
    """
    sources_str = ", ".join(data_sources)
    return f"{report_type} report generated using: {sources_str}"
'''
    
    def _get_research_tools(self, member: TeamMember, spec: TeamSpecification) -> str:
        """Generate research tools."""
        return '''
@tool
def research_topic(topic: str, depth: str = "moderate") -> Dict[str, Any]:
    """
    Research a specific topic.
    
    Args:
        topic: Topic to research
        depth: Research depth (surface/moderate/deep)
    
    Returns:
        Research findings
    """
    return {
        "topic": topic,
        "key_findings": ["Finding 1", "Finding 2"],
        "sources": ["Source 1", "Source 2"],
        "confidence": "high"
    }


@tool
def validate_information(claim: str, sources: List[str]) -> Dict[str, Any]:
    """
    Validate information against sources.
    
    Args:
        claim: Claim to validate
        sources: Sources to check against
    
    Returns:
        Validation results
    """
    return {
        "claim": claim,
        "validity": "confirmed",
        "supporting_sources": sources[:2] if sources else [],
        "confidence": 0.85
    }
'''
    
    def _get_content_creation_tools(self, member: TeamMember, spec: TeamSpecification) -> str:
        """Generate content creation tools."""
        return '''
@tool
def create_content_outline(topic: str, content_type: str, target_audience: str) -> Dict[str, Any]:
    """
    Create a content outline.
    
    Args:
        topic: Content topic
        content_type: Type of content (blog/video/social)
        target_audience: Target audience
    
    Returns:
        Content outline
    """
    return {
        "topic": topic,
        "type": content_type,
        "audience": target_audience,
        "sections": ["Introduction", "Main Points", "Conclusion"],
        "estimated_length": "1500 words"
    }


@tool
def optimize_content(content: str, optimization_goal: str) -> Dict[str, Any]:
    """
    Optimize content for specific goals.
    
    Args:
        content: Content to optimize
        optimization_goal: Goal (SEO/engagement/clarity)
    
    Returns:
        Optimization suggestions
    """
    return {
        "goal": optimization_goal,
        "suggestions": [
            "Add more keywords",
            "Improve headline",
            "Add call-to-action"
        ],
        "readability_score": 8.5
    }
'''
    
    def _get_monitoring_tools(self, member: TeamMember, spec: TeamSpecification) -> str:
        """Generate monitoring tools."""
        return '''
@tool
def monitor_system_health(system_name: str) -> Dict[str, Any]:
    """
    Monitor system health metrics.
    
    Args:
        system_name: Name of system to monitor
    
    Returns:
        System health status
    """
    return {
        "system": system_name,
        "status": "healthy",
        "uptime": "99.9%",
        "alerts": [],
        "last_check": "2 minutes ago"
    }


@tool
def analyze_performance(component: str, metric: str) -> Dict[str, Any]:
    """
    Analyze performance metrics.
    
    Args:
        component: Component to analyze
        metric: Specific metric to check
    
    Returns:
        Performance analysis
    """
    return {
        "component": component,
        "metric": metric,
        "current_value": 85,
        "threshold": 80,
        "status": "acceptable",
        "trend": "stable"
    }
'''
    
    def _get_financial_tools(self, member: TeamMember, spec: TeamSpecification) -> str:
        """Generate financial tools."""
        return '''
@tool
def analyze_budget(project_id: str, include_forecast: bool = True) -> Dict[str, Any]:
    """
    Analyze project or department budget.
    
    Args:
        project_id: Project identifier
        include_forecast: Include forecast data
    
    Returns:
        Budget analysis
    """
    result = {
        "project": project_id,
        "allocated": 100000,
        "spent": 45000,
        "remaining": 55000,
        "burn_rate": "on track"
    }
    
    if include_forecast:
        result["forecast"] = {
            "projected_total": 95000,
            "confidence": "high",
            "risks": ["Potential vendor cost increase"]
        }
    
    return result


@tool
def calculate_roi(investment: float, returns: float, time_period: str) -> Dict[str, Any]:
    """
    Calculate return on investment.
    
    Args:
        investment: Initial investment amount
        returns: Expected or actual returns
        time_period: Time period for calculation
    
    Returns:
        ROI calculation results
    """
    roi_percentage = ((returns - investment) / investment) * 100
    
    return {
        "investment": investment,
        "returns": returns,
        "roi_percentage": round(roi_percentage, 2),
        "time_period": time_period,
        "break_even": "6 months"
    }
'''
    
    def _get_generic_tools(self, member: TeamMember) -> str:
        """Generate generic tools when no specific category matches."""
        return f'''
@tool
def perform_task(task_description: str, parameters: Dict[str, Any]) -> str:
    """
    Perform a generic task for {member.role}.
    
    Args:
        task_description: Description of the task
        parameters: Task parameters
    
    Returns:
        Task completion status
    """
    param_str = ", ".join(f"{{k}}={{v}}" for k, v in parameters.items())
    return f"Task completed: {{task_description}} with parameters: {{param_str}}"


@tool
def analyze_situation(context: str, factors: List[str]) -> Dict[str, Any]:
    """
    Analyze a situation based on given factors.
    
    Args:
        context: Situation context
        factors: Factors to consider
    
    Returns:
        Situation analysis
    """
    return {{
        "context": context,
        "factors_considered": factors,
        "assessment": "Favorable with minor risks",
        "recommendations": ["Proceed with caution", "Monitor factor 1 closely"]
    }}
'''
    
    def _generate_tools_registry(self, all_tools: set, spec: TeamSpecification) -> str:
        """Generate tools registry for dynamic tool loading."""
        return f'''"""
Tools registry for {spec.name}.

Maps agents to their available tools.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Tool mappings for each agent
AGENT_TOOLS = {{
'''
        
        # Add tool mappings for each member
        for member in spec.members:
            tools_list = "[]"
            if hasattr(member, 'tools') and member.tools:
                tools_list = str(member.tools)
            registry += f'    "{member.name}": {tools_list},\n'
        
        registry += '''}}

def get_tools_for_agent(agent_name: str) -> List[str]:
    """
    Get list of tools available for a specific agent.
    
    Args:
        agent_name: Name of the agent
    
    Returns:
        List of tool names available to the agent
    """
    tools = AGENT_TOOLS.get(agent_name, [])
    logger.info(f"Loading tools for {agent_name}: {tools}")
    return tools


def load_tool_modules(agent_name: str) -> Dict[str, Any]:
    """
    Dynamically load tool modules for an agent.
    
    Args:
        agent_name: Name of the agent
    
    Returns:
        Dictionary of loaded tool functions
    """
    tools = {}
    
    # Always load shared tools
    from . import shared_tools
    for attr in dir(shared_tools):
        if not attr.startswith('_'):
            obj = getattr(shared_tools, attr)
            if callable(obj) and hasattr(obj, 'name'):
                tools[obj.name] = obj
    
    # Load agent-specific tools if they exist
    try:
        agent_module = __import__(f"{agent_name}_tools", fromlist=["."])
        for attr in dir(agent_module):
            if not attr.startswith('_'):
                obj = getattr(agent_module, attr)
                if callable(obj) and hasattr(obj, 'name'):
                    tools[obj.name] = obj
    except ImportError:
        logger.debug(f"No specific tools module for {agent_name}")
    
    return tools
'''
        
        return registry