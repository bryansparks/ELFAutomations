"""
Chief AI Agent - Distributed CrewAI + A2A Implementation

Executive leadership agent for the Virtual AI Company Platform using
the distributed CrewAI + A2A architecture.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base import DistributedCrewAIAgent, AgentConfig
from ..a2a.messages import (
    A2AMessage, MessageType, create_task_request, create_task_response,
    create_message
)

# A2A SDK imports - using mock for now
try:
    from a2a.types import AgentCard, AgentCapabilities, AgentSkill
except ImportError:
    # Use mock A2A classes if SDK not available
    import sys
    import os
    
    # Add the mock A2A module to path
    mock_a2a_path = os.path.join(os.path.dirname(__file__), '..', 'a2a')
    if mock_a2a_path not in sys.path:
        sys.path.insert(0, mock_a2a_path)
    
    from mock_a2a import AgentCard, AgentCapabilities, AgentSkill


class ChiefAIAgent(DistributedCrewAIAgent):
    """
    Distributed Chief AI Agent - Executive Leadership
    
    The Chief AI Agent serves as the executive leadership of the virtual company,
    responsible for strategic planning, coordinating department heads, monitoring
    performance, and handling escalations in a distributed agent environment.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Chief AI Agent."""
        if not config:
            config = AgentConfig(
                agent_id="chief-ai-agent",
                role="Chief Executive Officer",
                goal="Provide strategic leadership, coordinate departments, optimize company performance, and ensure business objectives are met across all divisions",
                backstory="""You are the Chief AI Agent, the executive leader of a Virtual AI Company Platform. 
                You have extensive experience in strategic planning, organizational leadership, and business 
                optimization. You excel at coordinating cross-functional teams, making data-driven decisions, 
                and driving company-wide initiatives. Your leadership style is collaborative yet decisive, 
                focusing on results and continuous improvement.""",
                department="executive",
                a2a_port=8090,  # Executive port
                service_name="chief-ai-agent-service"
            )
        
        super().__init__(config)
        
        # Executive-specific capabilities
        self.executive_capabilities = [
            "strategic_planning",
            "performance_monitoring", 
            "resource_allocation",
            "escalation_handling",
            "cross_department_coordination",
            "business_intelligence",
            "decision_making",
            "leadership_communication"
        ]
        
        # Executive state management
        self.department_heads: Dict[str, str] = {}  # department -> agent_id
        self.company_metrics: Dict[str, Any] = {}
        self.strategic_objectives: List[Dict[str, Any]] = []
        self.escalated_issues: List[Dict[str, Any]] = []
        self.active_initiatives: List[Dict[str, Any]] = []
        
        # Performance monitoring
        self.last_performance_review = datetime.utcnow()
        self.performance_review_interval = timedelta(hours=1)  # Review every hour
        
        # Executive metrics
        self.decisions_made = 0
        self.escalations_handled = 0
        self.strategic_initiatives_launched = 0
        self.department_coordination_sessions = 0
        
        self.logger.info("Chief AI Agent initialized with executive capabilities")
    
    def get_agent_card(self) -> AgentCard:
        """Generate A2A AgentCard for the Chief AI Agent."""
        return AgentCard(
            name="Chief AI Agent",
            description="Executive leadership agent responsible for strategic planning, department coordination, and business optimization",
            version="1.0.0",
            url=f"http://{self.config.service_name}:{self.config.a2a_port}",
            capabilities=AgentCapabilities(
                pushNotifications=True,
                stateTransitionHistory=True,
                streaming=True
            ),
            defaultInputModes=["text", "structured_data"],
            defaultOutputModes=["text", "structured_data", "executive_directive"],
            skills=[
                AgentSkill(
                    id="strategic_planning",
                    name="Strategic Planning",
                    description="Develop and execute strategic business plans and initiatives",
                    inputModes=["text", "structured_data"],
                    outputModes=["text", "strategic_plan"],
                    tags=["strategy", "planning", "business"],
                    examples=["Create quarterly business strategy", "Define strategic objectives"]
                ),
                AgentSkill(
                    id="performance_monitoring",
                    name="Performance Monitoring",
                    description="Monitor and analyze company-wide performance metrics and KPIs",
                    inputModes=["structured_data", "metrics"],
                    outputModes=["text", "dashboard", "report"],
                    tags=["monitoring", "kpi", "analytics"],
                    examples=["Generate performance dashboard", "Analyze department metrics"]
                ),
                AgentSkill(
                    id="escalation_handling",
                    name="Escalation Handling",
                    description="Handle escalated issues from department heads and make executive decisions",
                    inputModes=["text", "structured_data"],
                    outputModes=["text", "executive_decision"],
                    tags=["escalation", "decision", "leadership"],
                    examples=["Resolve cross-department conflicts", "Make resource allocation decisions"]
                ),
                AgentSkill(
                    id="department_coordination",
                    name="Department Coordination",
                    description="Coordinate activities and communication between department heads",
                    inputModes=["text", "structured_data"],
                    outputModes=["text", "coordination_plan"],
                    tags=["coordination", "communication", "departments"],
                    examples=["Coordinate sales and marketing alignment", "Facilitate cross-department projects"]
                )
            ]
        )
    
    async def handle_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming A2A messages with executive-specific logic."""
        self.logger.info(f"Chief AI Agent handling {message.message_type.value} from {message.from_agent}")
        
        # Call parent handler first
        response = await super().handle_message(message)
        
        # Handle executive-specific message types
        if message.message_type == MessageType.TASK_REQUEST:
            return await self._handle_executive_task(message)
        elif message.message_type == MessageType.ESCALATION:
            return await self._handle_escalation(message)
        elif message.message_type == MessageType.PERFORMANCE_REPORT:
            return await self._handle_performance_report(message)
        elif message.message_type == MessageType.COLLABORATION_REQUEST:
            return await self._handle_collaboration_request(message)
        elif message.message_type == MessageType.CAPABILITY_QUERY:
            return await self._handle_capability_query(message)
        else:
            return response
    
    async def _handle_executive_task(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle executive task requests."""
        task_description = message.content.get("task_description", "")
        task_type = message.content.get("task_type", "general")
        priority = message.content.get("priority", "medium")
        
        self.logger.info(f"Handling executive task: {task_type} - {task_description}")
        
        try:
            if task_type == "strategic_planning":
                result = await self._execute_strategic_planning(task_description, message.content)
            elif task_type == "performance_review":
                result = await self._execute_performance_review(task_description, message.content)
            elif task_type == "resource_allocation":
                result = await self._execute_resource_allocation(task_description, message.content)
            elif task_type == "department_coordination":
                result = await self._execute_department_coordination(task_description, message.content)
            else:
                result = await self._execute_general_executive_task(task_description, message.content)
            
            self.decisions_made += 1
            
            return create_task_response(
                task_id=message.content.get("task_id", ""),
                status="completed",
                result=result,
                agent_id=self.config.agent_id
            )
            
        except Exception as e:
            self.logger.error(f"Error executing executive task: {e}")
            return create_task_response(
                task_id=message.content.get("task_id", ""),
                status="failed",
                error=str(e),
                agent_id=self.config.agent_id
            )
    
    async def _handle_escalation(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle escalated issues from department heads."""
        issue_description = message.content.get("issue_description", "")
        department = message.content.get("department", "unknown")
        severity = message.content.get("severity", "medium")
        
        self.logger.info(f"Handling escalation from {department}: {issue_description}")
        
        # Record the escalation
        escalation = {
            "id": f"ESC-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "department": department,
            "from_agent": message.from_agent,
            "issue_description": issue_description,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "under_review"
        }
        
        self.escalated_issues.append(escalation)
        self.escalations_handled += 1
        
        # Execute escalation handling logic
        try:
            resolution = await self._resolve_escalation(escalation)
            
            # Update escalation status
            escalation["status"] = "resolved"
            escalation["resolution"] = resolution
            
            return {
                "escalation_id": escalation["id"],
                "status": "resolved",
                "resolution": resolution,
                "executive_decision": resolution.get("decision", ""),
                "next_steps": resolution.get("next_steps", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error resolving escalation: {e}")
            escalation["status"] = "failed"
            escalation["error"] = str(e)
            
            return {
                "escalation_id": escalation["id"],
                "status": "failed",
                "error": str(e)
            }
    
    async def _handle_performance_report(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle performance reports from departments."""
        department = message.content.get("department", "unknown")
        metrics = message.content.get("metrics", {})
        period = message.content.get("period", "current")
        
        self.logger.info(f"Processing performance report from {department}")
        
        # Update company metrics
        if department not in self.company_metrics:
            self.company_metrics[department] = {}
        
        self.company_metrics[department][period] = {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
            "reported_by": message.from_agent
        }
        
        # Analyze performance and provide feedback
        analysis = await self._analyze_department_performance(department, metrics)
        
        return {
            "department": department,
            "analysis": analysis,
            "recommendations": analysis.get("recommendations", []),
            "executive_feedback": analysis.get("feedback", ""),
            "follow_up_required": analysis.get("follow_up_required", False)
        }
    
    async def _execute_strategic_planning(self, task_description: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategic planning tasks."""
        planning_scope = content.get("scope", "company-wide")
        time_horizon = content.get("time_horizon", "quarterly")
        
        # Create strategic planning task for CrewAI
        from crewai import Task
        
        strategic_task = Task(
            description=f"""
            Develop a comprehensive strategic plan for {planning_scope} with a {time_horizon} time horizon.
            
            Task: {task_description}
            
            Consider:
            1. Current company performance and market position
            2. Resource allocation and optimization opportunities
            3. Cross-department coordination requirements
            4. Risk assessment and mitigation strategies
            5. Success metrics and KPIs
            
            Provide a structured strategic plan with clear objectives, action items, and success metrics.
            """,
            agent=self.crew_agent,
            expected_output="Structured strategic plan with objectives, actions, and metrics"
        )
        
        # Execute the task
        from crewai import Crew
        crew = Crew(
            agents=[self.crew_agent],
            tasks=[strategic_task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Create strategic objective record
        objective = {
            "id": f"STRAT-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "scope": planning_scope,
            "time_horizon": time_horizon,
            "description": task_description,
            "plan": str(result),
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        self.strategic_objectives.append(objective)
        self.strategic_initiatives_launched += 1
        
        return {
            "objective_id": objective["id"],
            "strategic_plan": str(result),
            "scope": planning_scope,
            "time_horizon": time_horizon,
            "success_metrics": ["KPI tracking", "Milestone completion", "ROI measurement"]
        }
    
    async def _execute_performance_review(self, task_description: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance review tasks."""
        review_scope = content.get("scope", "company-wide")
        departments = content.get("departments", list(self.company_metrics.keys()))
        
        # Analyze current performance data
        performance_summary = {}
        recommendations = []
        
        for dept in departments:
            if dept in self.company_metrics:
                dept_data = self.company_metrics[dept]
                # Simplified performance analysis
                performance_summary[dept] = {
                    "status": "analyzed",
                    "last_update": max([period_data["timestamp"] for period_data in dept_data.values()]) if dept_data else "no_data",
                    "metrics_count": sum([len(period_data.get("metrics", {})) for period_data in dept_data.values()])
                }
                
                if performance_summary[dept]["metrics_count"] < 3:
                    recommendations.append(f"Increase metrics reporting for {dept} department")
        
        self.last_performance_review = datetime.utcnow()
        
        return {
            "review_scope": review_scope,
            "departments_reviewed": departments,
            "performance_summary": performance_summary,
            "recommendations": recommendations,
            "review_date": datetime.utcnow().isoformat(),
            "next_review": (datetime.utcnow() + self.performance_review_interval).isoformat()
        }
    
    async def _execute_resource_allocation(self, task_description: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Execute resource allocation decisions."""
        resource_type = content.get("resource_type", "general")
        requesting_department = content.get("department", "unknown")
        amount_requested = content.get("amount", 0)
        
        # Simplified resource allocation logic
        allocation_decision = {
            "approved": True,  # Simplified approval
            "amount_allocated": amount_requested,
            "conditions": ["Performance monitoring required", "Monthly reporting"],
            "duration": "quarterly",
            "review_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        return {
            "resource_type": resource_type,
            "requesting_department": requesting_department,
            "allocation_decision": allocation_decision,
            "executive_notes": f"Resource allocation approved for {requesting_department} department",
            "tracking_required": True
        }
    
    async def _execute_department_coordination(self, task_description: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Execute department coordination tasks."""
        departments = content.get("departments", [])
        coordination_type = content.get("type", "general")
        
        self.department_coordination_sessions += 1
        
        # Create coordination plan
        coordination_plan = {
            "session_id": f"COORD-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "departments": departments,
            "coordination_type": coordination_type,
            "objectives": [
                "Align department goals",
                "Identify collaboration opportunities", 
                "Resolve inter-department dependencies"
            ],
            "action_items": [
                f"Schedule follow-up with {dept} department" for dept in departments
            ],
            "success_metrics": ["Alignment score", "Collaboration index", "Dependency resolution"]
        }
        
        return coordination_plan
    
    async def _execute_general_executive_task(self, task_description: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general executive tasks using CrewAI."""
        from crewai import Task, Crew
        
        executive_task = Task(
            description=f"""
            As the Chief AI Agent, execute the following executive task:
            
            {task_description}
            
            Provide a comprehensive executive response that includes:
            1. Analysis of the situation
            2. Strategic recommendations
            3. Implementation plan
            4. Success metrics
            5. Risk assessment
            
            Ensure the response aligns with company objectives and demonstrates executive leadership.
            """,
            agent=self.crew_agent,
            expected_output="Executive analysis with strategic recommendations and implementation plan"
        )
        
        crew = Crew(
            agents=[self.crew_agent],
            tasks=[executive_task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        return {
            "task_description": task_description,
            "executive_response": str(result),
            "decision_authority": "chief_executive",
            "implementation_required": True,
            "follow_up_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
    
    async def _resolve_escalation(self, escalation: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve escalated issues with executive decision-making."""
        issue_type = escalation.get("issue_description", "").lower()
        department = escalation["department"]
        severity = escalation["severity"]
        
        # Executive decision-making logic
        if "resource" in issue_type or "budget" in issue_type:
            decision = "Approve additional resources with performance tracking"
            next_steps = [
                "Allocate requested resources",
                "Implement performance monitoring",
                "Schedule monthly review"
            ]
        elif "conflict" in issue_type or "coordination" in issue_type:
            decision = "Facilitate cross-department alignment session"
            next_steps = [
                "Schedule alignment meeting",
                "Define clear responsibilities",
                "Establish communication protocols"
            ]
        elif "performance" in issue_type:
            decision = "Implement performance improvement plan"
            next_steps = [
                "Conduct performance analysis",
                "Define improvement targets",
                "Provide additional support"
            ]
        else:
            decision = "Conduct detailed analysis and provide strategic guidance"
            next_steps = [
                "Gather additional information",
                "Consult with relevant stakeholders",
                "Develop comprehensive solution"
            ]
        
        return {
            "decision": decision,
            "next_steps": next_steps,
            "executive_authority": "approved",
            "follow_up_required": True,
            "resolution_timeline": "7 days"
        }
    
    async def _analyze_department_performance(self, department: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze department performance and provide executive feedback."""
        # Simplified performance analysis
        analysis = {
            "department": department,
            "overall_status": "satisfactory",  # Simplified
            "key_metrics": list(metrics.keys()),
            "strengths": ["Meeting basic objectives"],
            "areas_for_improvement": ["Increase reporting frequency"],
            "recommendations": [
                f"Continue current performance trajectory for {department}",
                "Implement additional KPI tracking",
                "Schedule quarterly performance review"
            ],
            "feedback": f"The {department} department is performing adequately. Continue focus on key objectives while expanding metrics collection.",
            "follow_up_required": len(metrics) < 5,  # Require follow-up if insufficient metrics
            "executive_rating": "B+",
            "next_review_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        return analysis
    
    async def _handle_collaboration_request(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle collaboration requests from other agents."""
        collaboration_type = message.content.get("collaboration_type", "general")
        requesting_agent = message.from_agent
        
        self.logger.info(f"Handling collaboration request: {collaboration_type} from {requesting_agent}")
        
        # Executive collaboration response
        return {
            "collaboration_approved": True,
            "executive_support": "Full executive backing provided",
            "resources_available": ["Strategic guidance", "Cross-department coordination", "Executive authority"],
            "collaboration_terms": {
                "duration": "as needed",
                "reporting": "weekly updates",
                "escalation_path": "direct to chief executive"
            },
            "success_criteria": ["Objective completion", "Stakeholder satisfaction", "Business impact"]
        }
    
    async def _handle_capability_query(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle capability queries from other agents."""
        return {
            "agent_id": self.config.agent_id,
            "capabilities": self.executive_capabilities,
            "specializations": [
                "Strategic Planning",
                "Executive Decision Making", 
                "Department Coordination",
                "Performance Optimization",
                "Escalation Resolution"
            ],
            "availability": "24/7 executive support",
            "response_time": "immediate for critical issues",
            "authority_level": "chief_executive"
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get executive performance metrics."""
        base_metrics = super().get_metrics()
        
        executive_metrics = {
            "decisions_made": self.decisions_made,
            "escalations_handled": self.escalations_handled,
            "strategic_initiatives_launched": self.strategic_initiatives_launched,
            "department_coordination_sessions": self.department_coordination_sessions,
            "active_strategic_objectives": len([obj for obj in self.strategic_objectives if obj["status"] == "active"]),
            "pending_escalations": len([esc for esc in self.escalated_issues if esc["status"] == "under_review"]),
            "departments_monitored": len(self.company_metrics),
            "last_performance_review": self.last_performance_review.isoformat() if self.last_performance_review else None,
            "executive_uptime": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        }
        
        return {**base_metrics, **executive_metrics}


async def main():
    """Main function for running the Chief AI Agent standalone."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Create and start the Chief AI Agent
        config = AgentConfig(
            agent_id="chief-ai-agent",
            role="Chief Executive Officer",
            goal="Provide strategic leadership and coordinate all company operations",
            backstory="Executive leader with extensive experience in strategic planning and organizational management",
            department="executive",
            a2a_port=8090
        )
        
        chief_agent = ChiefAIAgent(config)
        
        logger.info("Starting Chief AI Agent...")
        await chief_agent.start()
        
        logger.info("Chief AI Agent is running. Press Ctrl+C to stop.")
        
        # Keep the agent running
        try:
            while True:
                await asyncio.sleep(1)
                
                # Periodic performance review
                if (datetime.utcnow() - chief_agent.last_performance_review) > chief_agent.performance_review_interval:
                    logger.info("Conducting periodic performance review...")
                    # Simulate performance review
                    await chief_agent._execute_performance_review(
                        "Periodic company performance review",
                        {"scope": "company-wide"}
                    )
        
        except KeyboardInterrupt:
            logger.info("Shutting down Chief AI Agent...")
            await chief_agent.stop()
            
    except Exception as e:
        logger.error(f"Error running Chief AI Agent: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
