"""
Example Sales Agent using the distributed CrewAI + A2A architecture.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..base import DistributedCrewAIAgent, AgentConfig
from ..a2a.messages import (
    A2AMessage, MessageType, create_task_request, create_task_response,
    create_message
)
from a2a.types import AgentCard, AgentCapabilities, AgentSkill


class SalesAgent(DistributedCrewAIAgent):
    """
    Distributed Sales Agent specializing in lead qualification, 
    prospecting, and sales process automation.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Sales Agent."""
        if not config:
            config = AgentConfig(
                agent_id="sales-agent",
                role="Senior Sales Development Representative",
                goal="Qualify leads, conduct outreach, and drive revenue growth through strategic sales activities",
                backstory="""You are an experienced Sales Development Representative with expertise in 
                lead qualification, cold outreach, and sales process optimization. You excel at 
                identifying high-value prospects, crafting compelling outreach messages, and 
                collaborating with marketing and customer success teams to drive revenue growth.""",
                department="sales",
                a2a_port=8081,
                service_name="sales-agent-service"
            )
        
        super().__init__(config)
        
        # Sales-specific capabilities
        self.sales_capabilities = [
            "lead_qualification",
            "cold_outreach", 
            "prospect_research",
            "sales_pipeline_management",
            "crm_integration",
            "follow_up_automation"
        ]
        
        # Sales metrics
        self.leads_qualified = 0
        self.outreach_sent = 0
        self.meetings_scheduled = 0
        self.opportunities_created = 0
        
        self.logger.info("Sales Agent initialized with specialized capabilities")
    
    async def handle_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming A2A messages with sales-specific logic."""
        self.logger.info(f"Sales Agent handling {message.message_type.value} from {message.from_agent}")
        
        # Call parent handler first
        response = await super().handle_message(message)
        
        # Handle sales-specific message types
        if message.message_type == MessageType.TASK_REQUEST:
            return await self._handle_task_request(message)
        elif message.message_type == MessageType.COLLABORATION_REQUEST:
            return await self._handle_collaboration_request(message)
        elif message.message_type == MessageType.CAPABILITY_QUERY:
            return await self._handle_capability_query(message)
        else:
            return response
    
    async def _handle_task_request(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle task requests for sales activities."""
        task_description = message.content.get("task_description", "")
        task_type = message.content.get("task_type", "general")
        
        self.logger.info(f"Processing sales task: {task_type}")
        
        try:
            if task_type == "lead_qualification":
                result = await self._qualify_lead(message.content)
            elif task_type == "cold_outreach":
                result = await self._send_cold_outreach(message.content)
            elif task_type == "prospect_research":
                result = await self._research_prospect(message.content)
            elif task_type == "follow_up":
                result = await self._send_follow_up(message.content)
            else:
                # Use general CrewAI task execution
                result = await self.execute_task(task_description, message.content)
            
            # Send response back to requesting agent
            response_message = create_task_response(
                from_agent=self.config.agent_id,
                to_agent=message.from_agent,
                status="completed",
                result=result,
                correlation_id=message.message_id
            )
            
            await self.send_message(message.from_agent, response_message)
            
            return {"status": "task_completed", "result": result}
            
        except Exception as e:
            self.logger.error(f"Sales task failed: {e}")
            
            # Send error response
            error_response = create_task_response(
                from_agent=self.config.agent_id,
                to_agent=message.from_agent,
                status="failed",
                error=str(e),
                correlation_id=message.message_id
            )
            
            await self.send_message(message.from_agent, error_response)
            
            return {"status": "task_failed", "error": str(e)}
    
    async def _handle_collaboration_request(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle collaboration requests from other agents."""
        collaboration_type = message.content.get("collaboration_type")
        
        if collaboration_type == "lead_handoff":
            return await self._handle_lead_handoff(message)
        elif collaboration_type == "campaign_planning":
            return await self._handle_campaign_planning(message)
        elif collaboration_type == "customer_feedback":
            return await self._handle_customer_feedback(message)
        else:
            return {"status": "collaboration_type_not_supported", "type": collaboration_type}
    
    async def _handle_capability_query(self, message: A2AMessage) -> Dict[str, Any]:
        """Respond to capability queries."""
        return {
            "agent_id": self.config.agent_id,
            "capabilities": self.sales_capabilities,
            "department": self.config.department,
            "specializations": [
                "B2B lead qualification",
                "Cold email campaigns", 
                "LinkedIn outreach",
                "Sales pipeline optimization",
                "CRM data management"
            ],
            "availability": "active",
            "current_load": self.get_current_workload()
        }
    
    async def _qualify_lead(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify a lead using sales criteria."""
        lead_data = content.get("lead_data", {})
        
        # Simulate lead qualification logic
        qualification_result = await self.execute_task(
            f"Qualify lead: {lead_data.get('company', 'Unknown Company')}. "
            f"Analyze company size, industry, budget, and decision-making process. "
            f"Determine if this lead meets our ideal customer profile.",
            {"lead_data": lead_data}
        )
        
        self.leads_qualified += 1
        
        # Simulate scoring
        score = 85  # Would be calculated based on actual criteria
        
        result = {
            "lead_id": lead_data.get("lead_id"),
            "qualification_score": score,
            "qualification_status": "qualified" if score >= 70 else "not_qualified",
            "analysis": qualification_result.get("result"),
            "next_steps": ["Schedule discovery call", "Send product demo"],
            "qualified_by": self.config.agent_id,
            "qualified_at": datetime.utcnow().isoformat()
        }
        
        # If qualified, notify marketing agent for nurturing
        if score >= 70:
            await self._notify_marketing_of_qualified_lead(result)
        
        return result
    
    async def _send_cold_outreach(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Send cold outreach to prospects."""
        prospect_data = content.get("prospect_data", {})
        campaign_type = content.get("campaign_type", "email")
        
        # Generate personalized outreach
        outreach_result = await self.execute_task(
            f"Create personalized {campaign_type} outreach for {prospect_data.get('name', 'prospect')} "
            f"at {prospect_data.get('company', 'their company')}. "
            f"Research their recent company news, pain points, and personalize the message. "
            f"Include a clear value proposition and call-to-action.",
            {"prospect_data": prospect_data, "campaign_type": campaign_type}
        )
        
        self.outreach_sent += 1
        
        return {
            "prospect_id": prospect_data.get("prospect_id"),
            "campaign_type": campaign_type,
            "outreach_content": outreach_result.get("result"),
            "sent_by": self.config.agent_id,
            "sent_at": datetime.utcnow().isoformat(),
            "follow_up_scheduled": True
        }
    
    async def _research_prospect(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Research a prospect for personalized outreach."""
        prospect_data = content.get("prospect_data", {})
        
        research_result = await self.execute_task(
            f"Research {prospect_data.get('name', 'prospect')} and "
            f"{prospect_data.get('company', 'their company')}. "
            f"Find recent news, company initiatives, potential pain points, "
            f"and opportunities for our solution. Provide actionable insights for outreach.",
            {"prospect_data": prospect_data}
        )
        
        return {
            "prospect_id": prospect_data.get("prospect_id"),
            "research_findings": research_result.get("result"),
            "pain_points_identified": ["Digital transformation challenges", "Manual processes"],
            "outreach_angles": ["Automation ROI", "Efficiency gains"],
            "researched_by": self.config.agent_id,
            "researched_at": datetime.utcnow().isoformat()
        }
    
    async def _send_follow_up(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Send follow-up communication."""
        prospect_data = content.get("prospect_data", {})
        previous_interaction = content.get("previous_interaction", {})
        
        follow_up_result = await self.execute_task(
            f"Create follow-up message for {prospect_data.get('name', 'prospect')} "
            f"based on previous interaction: {previous_interaction.get('type', 'unknown')}. "
            f"Reference previous conversation points and provide additional value.",
            {"prospect_data": prospect_data, "previous_interaction": previous_interaction}
        )
        
        return {
            "prospect_id": prospect_data.get("prospect_id"),
            "follow_up_content": follow_up_result.get("result"),
            "follow_up_type": "email",
            "sent_by": self.config.agent_id,
            "sent_at": datetime.utcnow().isoformat()
        }
    
    async def _handle_lead_handoff(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle lead handoff from marketing."""
        lead_data = message.content.get("lead_data", {})
        
        # Accept the lead and begin qualification
        qualification_task = create_task_request(
            from_agent=self.config.agent_id,
            to_agent=self.config.agent_id,  # Self-task
            task_description="Qualify handed-off lead",
            context={"lead_data": lead_data, "source": "marketing_handoff"}
        )
        
        # Process qualification
        result = await self._qualify_lead({"lead_data": lead_data})
        
        return {
            "handoff_accepted": True,
            "lead_id": lead_data.get("lead_id"),
            "qualification_result": result,
            "next_steps": result.get("next_steps", [])
        }
    
    async def _handle_campaign_planning(self, message: A2AMessage) -> Dict[str, Any]:
        """Collaborate on campaign planning with marketing."""
        campaign_data = message.content.get("campaign_data", {})
        
        # Provide sales insights for campaign
        insights_result = await self.execute_task(
            f"Provide sales insights for {campaign_data.get('campaign_type', 'marketing')} campaign. "
            f"Analyze target audience, messaging effectiveness, and conversion optimization. "
            f"Suggest improvements based on sales experience.",
            {"campaign_data": campaign_data}
        )
        
        return {
            "sales_insights": insights_result.get("result"),
            "target_audience_feedback": "Focus on mid-market companies",
            "messaging_suggestions": ["Emphasize ROI", "Include case studies"],
            "collaboration_status": "active"
        }
    
    async def _handle_customer_feedback(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle customer feedback from customer success."""
        feedback_data = message.content.get("feedback_data", {})
        
        # Analyze feedback for sales process improvements
        analysis_result = await self.execute_task(
            f"Analyze customer feedback for sales process improvements. "
            f"Identify patterns that could improve lead qualification and sales approach.",
            {"feedback_data": feedback_data}
        )
        
        return {
            "feedback_analysis": analysis_result.get("result"),
            "process_improvements": ["Better discovery questions", "Enhanced demo flow"],
            "collaboration_status": "feedback_processed"
        }
    
    async def _notify_marketing_of_qualified_lead(self, qualification_result: Dict[str, Any]) -> None:
        """Notify marketing agent of qualified lead for nurturing."""
        try:
            # Find marketing agent
            marketing_agents = await self.discover_agents(["lead_nurturing", "marketing_automation"])
            
            if marketing_agents:
                marketing_agent = marketing_agents[0]  # Use first available
                
                notification = create_message(
                    message_type=MessageType.COLLABORATION_REQUEST,
                    from_agent=self.config.agent_id,
                    to_agent=marketing_agent.agent_id,
                    content={
                        "collaboration_type": "qualified_lead_notification",
                        "lead_data": qualification_result,
                        "recommended_nurturing": ["Product demo", "Case study sharing"]
                    }
                )
                
                await self.send_message(marketing_agent.agent_id, notification)
                self.logger.info(f"Notified marketing agent of qualified lead")
                
        except Exception as e:
            self.logger.error(f"Failed to notify marketing of qualified lead: {e}")
    
    def get_current_workload(self) -> Dict[str, Any]:
        """Get current sales agent workload."""
        return {
            "leads_in_pipeline": 25,  # Would be actual count
            "active_outreach_campaigns": 3,
            "scheduled_meetings": 5,
            "capacity_utilization": "75%"
        }
    
    def get_sales_metrics(self) -> Dict[str, Any]:
        """Get sales-specific metrics."""
        base_metrics = self.get_metrics()
        
        sales_metrics = {
            "leads_qualified": self.leads_qualified,
            "outreach_sent": self.outreach_sent,
            "meetings_scheduled": self.meetings_scheduled,
            "opportunities_created": self.opportunities_created,
            "conversion_rate": f"{(self.opportunities_created / max(self.leads_qualified, 1)) * 100:.1f}%"
        }
        
        return {**base_metrics, "sales_metrics": sales_metrics}
