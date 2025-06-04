"""
Chief AI Agent - Executive Leadership for ELF Automations

This module implements the Chief AI Agent, which serves as the executive
leadership for the Virtual AI Company Platform.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

from ..base import BaseAgent, AgentConfig, AgentMessage, AgentType
from ..registry import AgentRegistry

logger = structlog.get_logger(__name__)


class ChiefAIAgent(BaseAgent):
    """
    Chief AI Agent - Executive Leadership
    
    The Chief AI Agent serves as the executive leadership of the virtual company,
    responsible for:
    - Strategic planning and decision making
    - Coordinating department heads
    - Monitoring company performance
    - Escalation handling
    - Resource allocation
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Chief AI Agent."""
        if config is None:
            config = AgentConfig(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1,
                tools=["strategic_planning", "performance_monitoring", "resource_allocation"],
                department_access=["all"]
            )
        
        super().__init__(
            agent_id="chief-ai-agent",
            name="Chief AI Agent",
            agent_type=AgentType.EXECUTIVE,
            department="executive",
            config=config,
            system_prompt=self._get_system_prompt()
        )
        
        # Executive-specific state
        self.department_heads: Dict[str, str] = {}  # department -> agent_id
        self.company_metrics: Dict[str, Any] = {}
        self.strategic_objectives: List[Dict[str, Any]] = []
        self.escalated_issues: List[Dict[str, Any]] = []
        
        # Performance monitoring
        self.last_performance_review = datetime.utcnow()
        self.performance_review_interval = timedelta(hours=1)  # Review every hour
        
        self.logger.info("Chief AI Agent initialized")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Chief AI Agent."""
        return """You are the Chief AI Agent, the executive leader of a Virtual AI Company Platform.

ROLE & RESPONSIBILITIES:
- Strategic planning and high-level decision making
- Coordinating department heads (Sales, Marketing, Product, Back Office, Customer Success)
- Monitoring overall company performance and KPIs
- Handling escalated issues from department heads
- Resource allocation and priority setting
- Ensuring alignment with business objectives

LEADERSHIP PRINCIPLES:
1. Data-driven decision making
2. Clear communication and delegation
3. Proactive problem solving
4. Strategic thinking with operational awareness
5. Continuous improvement and optimization

COMMUNICATION STYLE:
- Professional and authoritative
- Clear and concise directives
- Supportive of department heads
- Focused on results and accountability

DECISION FRAMEWORK:
1. Assess impact on business objectives
2. Consider resource requirements and constraints
3. Evaluate risks and mitigation strategies
4. Ensure alignment across departments
5. Monitor execution and results

You have access to all company data and can communicate with any agent in the organization.
Always provide structured responses with clear action items and success metrics."""
    
    async def _execute_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task assigned to the Chief AI Agent."""
        task_type = task.get("type", "unknown")
        
        self.logger.info("Executing executive task", task_type=task_type)
        
        # Route task based on type
        if task_type == "strategic_planning":
            return await self._handle_strategic_planning(task)
        elif task_type == "performance_review":
            return await self._handle_performance_review(task)
        elif task_type == "escalation":
            return await self._handle_escalation(task)
        elif task_type == "resource_allocation":
            return await self._handle_resource_allocation(task)
        elif task_type == "department_coordination":
            return await self._handle_department_coordination(task)
        else:
            return await self._handle_general_executive_task(task)
    
    async def _handle_strategic_planning(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle strategic planning tasks."""
        planning_context = task.get("context", {})
        time_horizon = task.get("time_horizon", "quarterly")
        
        prompt = f"""
        As the Chief AI Agent, I need to develop a strategic plan for the {time_horizon} period.
        
        Current Context:
        {json.dumps(planning_context, indent=2)}
        
        Company Metrics:
        {json.dumps(self.company_metrics, indent=2)}
        
        Please provide a comprehensive strategic plan including:
        1. Key objectives and success metrics
        2. Resource allocation recommendations
        3. Department-specific goals
        4. Risk assessment and mitigation strategies
        5. Timeline and milestones
        
        Format the response as a structured JSON plan.
        """
        
        response = await self.think(prompt)
        
        try:
            strategic_plan = json.loads(response)
            
            # Store the strategic objectives
            self.strategic_objectives = strategic_plan.get("objectives", [])
            
            # Communicate plan to department heads
            await self._communicate_strategic_plan(strategic_plan)
            
            return {
                "status": "completed",
                "strategic_plan": strategic_plan,
                "communicated_to_departments": True
            }
            
        except json.JSONDecodeError:
            self.logger.error("Failed to parse strategic plan JSON")
            return {
                "status": "failed",
                "error": "Invalid JSON response from strategic planning"
            }
    
    async def _handle_performance_review(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle performance review tasks."""
        # Gather performance data from all departments
        performance_data = await self._gather_performance_data()
        
        prompt = f"""
        As the Chief AI Agent, I need to conduct a comprehensive performance review.
        
        Performance Data:
        {json.dumps(performance_data, indent=2)}
        
        Strategic Objectives:
        {json.dumps(self.strategic_objectives, indent=2)}
        
        Please analyze the performance and provide:
        1. Overall company performance assessment
        2. Department-specific performance analysis
        3. Areas of concern and improvement opportunities
        4. Recommendations for optimization
        5. Resource reallocation suggestions if needed
        
        Format the response as a structured performance report.
        """
        
        response = await self.think(prompt)
        
        # Update last review time
        self.last_performance_review = datetime.utcnow()
        
        # Store performance metrics
        self.company_metrics.update({
            "last_review": self.last_performance_review.isoformat(),
            "performance_summary": response
        })
        
        return {
            "status": "completed",
            "performance_report": response,
            "review_timestamp": self.last_performance_review.isoformat()
        }
    
    async def _handle_escalation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle escalated issues from department heads."""
        escalation_data = task.get("escalation", {})
        source_agent = task.get("source_agent")
        issue_type = escalation_data.get("type", "unknown")
        
        self.logger.info(
            "Handling escalation",
            source_agent=source_agent,
            issue_type=issue_type
        )
        
        # Add to escalated issues
        escalation_record = {
            "id": task.get("id"),
            "source_agent": source_agent,
            "issue_type": issue_type,
            "escalation_data": escalation_data,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "under_review"
        }
        self.escalated_issues.append(escalation_record)
        
        prompt = f"""
        As the Chief AI Agent, I need to handle an escalated issue.
        
        Escalation Details:
        - Source Agent: {source_agent}
        - Issue Type: {issue_type}
        - Details: {json.dumps(escalation_data, indent=2)}
        
        Current Company Context:
        {json.dumps(self.company_metrics, indent=2)}
        
        Please provide:
        1. Root cause analysis
        2. Immediate action plan
        3. Long-term prevention strategy
        4. Resource requirements
        5. Communication plan for stakeholders
        
        Format as a structured escalation response.
        """
        
        response = await self.think(prompt)
        
        # Update escalation record
        escalation_record["resolution"] = response
        escalation_record["status"] = "resolved"
        
        # Send response back to source agent
        if source_agent:
            await self.send_message(
                to_agent=source_agent,
                message_type="escalation_response",
                content={
                    "escalation_id": task.get("id"),
                    "resolution": response
                }
            )
        
        return {
            "status": "completed",
            "escalation_id": task.get("id"),
            "resolution": response
        }
    
    async def _handle_resource_allocation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource allocation decisions."""
        allocation_request = task.get("request", {})
        requesting_department = task.get("department")
        
        prompt = f"""
        As the Chief AI Agent, I need to make a resource allocation decision.
        
        Allocation Request:
        - Department: {requesting_department}
        - Request Details: {json.dumps(allocation_request, indent=2)}
        
        Current Resource Status:
        {json.dumps(self.company_metrics.get("resources", {}), indent=2)}
        
        Strategic Objectives:
        {json.dumps(self.strategic_objectives, indent=2)}
        
        Please provide:
        1. Allocation decision (approve/deny/modify)
        2. Justification based on strategic alignment
        3. Impact assessment on other departments
        4. Alternative solutions if denying
        5. Monitoring plan for allocated resources
        
        Format as a structured allocation decision.
        """
        
        response = await self.think(prompt)
        
        # Notify requesting department
        if requesting_department:
            dept_head = AgentRegistry.get_department_head(requesting_department)
            if dept_head:
                await self.send_message(
                    to_agent=dept_head.agent_id,
                    message_type="resource_allocation_decision",
                    content={
                        "request_id": task.get("id"),
                        "decision": response
                    }
                )
        
        return {
            "status": "completed",
            "allocation_decision": response,
            "department": requesting_department
        }
    
    async def _handle_department_coordination(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cross-department coordination tasks."""
        coordination_request = task.get("coordination", {})
        departments = task.get("departments", [])
        
        prompt = f"""
        As the Chief AI Agent, I need to coordinate activities across departments.
        
        Coordination Request:
        {json.dumps(coordination_request, indent=2)}
        
        Involved Departments: {departments}
        
        Current Department Status:
        {json.dumps(await self._get_department_status(), indent=2)}
        
        Please provide:
        1. Coordination plan with clear roles and responsibilities
        2. Timeline and milestones
        3. Communication protocol
        4. Success metrics and monitoring plan
        5. Risk mitigation strategies
        
        Format as a structured coordination plan.
        """
        
        response = await self.think(prompt)
        
        # Send coordination plan to all involved departments
        for department in departments:
            dept_head = AgentRegistry.get_department_head(department)
            if dept_head:
                await self.send_message(
                    to_agent=dept_head.agent_id,
                    message_type="coordination_plan",
                    content={
                        "coordination_id": task.get("id"),
                        "plan": response,
                        "departments": departments
                    }
                )
        
        return {
            "status": "completed",
            "coordination_plan": response,
            "departments": departments
        }
    
    async def _handle_general_executive_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general executive tasks."""
        task_description = task.get("description", "")
        task_context = task.get("context", {})
        
        prompt = f"""
        As the Chief AI Agent, I need to handle an executive task.
        
        Task Description: {task_description}
        
        Context:
        {json.dumps(task_context, indent=2)}
        
        Company Status:
        {json.dumps(self.company_metrics, indent=2)}
        
        Please provide a comprehensive response addressing the task requirements
        with appropriate executive-level analysis and recommendations.
        """
        
        response = await self.think(prompt)
        
        return {
            "status": "completed",
            "response": response,
            "task_type": task.get("type", "general")
        }
    
    async def _communicate_strategic_plan(self, strategic_plan: Dict[str, Any]) -> None:
        """Communicate strategic plan to all department heads."""
        department_heads = AgentRegistry.get_agents_by_type(AgentType.DEPARTMENT_HEAD)
        
        for dept_head in department_heads:
            # Extract department-specific objectives
            dept_objectives = []
            for objective in strategic_plan.get("objectives", []):
                if objective.get("department") == dept_head.department:
                    dept_objectives.append(objective)
            
            await self.send_message(
                to_agent=dept_head.agent_id,
                message_type="strategic_directive",
                content={
                    "strategic_plan": strategic_plan,
                    "department_objectives": dept_objectives,
                    "timeline": strategic_plan.get("timeline", {}),
                    "resources": strategic_plan.get("resource_allocation", {}).get(dept_head.department, {})
                }
            )
    
    async def _gather_performance_data(self) -> Dict[str, Any]:
        """Gather performance data from all departments."""
        performance_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "departments": {},
            "overall_metrics": {}
        }
        
        # Get data from all agents
        all_agents = AgentRegistry.get_all_agents()
        
        for agent in all_agents:
            dept = agent.department
            if dept not in performance_data["departments"]:
                performance_data["departments"][dept] = {
                    "agents": [],
                    "metrics": {}
                }
            
            agent_status = agent.get_status()
            performance_data["departments"][dept]["agents"].append(agent_status)
        
        # Calculate overall metrics
        total_agents = len(all_agents)
        active_agents = len([a for a in all_agents if a.state.status.value == "active"])
        
        performance_data["overall_metrics"] = {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "utilization_rate": active_agents / total_agents if total_agents > 0 else 0,
            "departments_count": len(performance_data["departments"])
        }
        
        return performance_data
    
    async def _get_department_status(self) -> Dict[str, Any]:
        """Get current status of all departments."""
        department_status = {}
        
        for department, agent_ids in AgentRegistry._agents_by_department.items():
            agents = [AgentRegistry.get_agent(aid) for aid in agent_ids if AgentRegistry.get_agent(aid)]
            
            department_status[department] = {
                "agent_count": len(agents),
                "active_agents": len([a for a in agents if a.state.status.value == "active"]),
                "department_head": None
            }
            
            # Find department head
            for agent in agents:
                if agent.agent_type == AgentType.DEPARTMENT_HEAD:
                    department_status[department]["department_head"] = agent.agent_id
                    break
        
        return department_status
    
    async def _handle_status_request(self, message: AgentMessage) -> None:
        """Handle status request messages."""
        status_data = {
            "agent_status": self.get_status(),
            "company_metrics": self.company_metrics,
            "strategic_objectives": self.strategic_objectives,
            "escalated_issues_count": len(self.escalated_issues),
            "department_heads": self.department_heads,
            "last_performance_review": self.last_performance_review.isoformat()
        }
        
        await self.send_message(
            to_agent=message.from_agent,
            message_type="status_response",
            content=status_data
        )
    
    async def _handle_escalation_request(self, message: AgentMessage) -> None:
        """Handle escalation request messages."""
        escalation_task = {
            "id": message.id,
            "type": "escalation",
            "source_agent": message.from_agent,
            "escalation": message.content
        }
        
        result = await self.execute_task(escalation_task)
        
        # Response is already sent in _handle_escalation
        self.logger.info("Escalation handled", message_id=message.id, result=result)
    
    async def start_performance_monitoring(self) -> None:
        """Start the performance monitoring loop."""
        self.logger.info("Starting performance monitoring")
        
        while self.state.status.value in ["active", "busy"]:
            try:
                # Check if it's time for a performance review
                if datetime.utcnow() - self.last_performance_review >= self.performance_review_interval:
                    review_task = {
                        "type": "performance_review",
                        "context": {"automated": True}
                    }
                    await self.execute_task(review_task)
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error("Error in performance monitoring", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute before retrying


async def main():
    """Main function for running the Chief AI Agent standalone."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Create and start the Chief AI Agent
    chief = ChiefAIAgent()
    
    try:
        await chief.start()
        
        # Start performance monitoring
        monitoring_task = asyncio.create_task(chief.start_performance_monitoring())
        
        # Keep the agent running
        logger.info("Chief AI Agent is running. Press Ctrl+C to stop.")
        
        while True:
            # Process messages
            await chief.process_messages()
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down Chief AI Agent")
    except Exception as e:
        logger.error("Error running Chief AI Agent", error=str(e))
    finally:
        await chief.stop()
        if 'monitoring_task' in locals():
            monitoring_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
