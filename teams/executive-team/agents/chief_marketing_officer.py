#!/usr/bin/env python3
"""
Chief Marketing Officer Agent for executive-team
"""

from crewai import Agent
from typing import Optional, List, Dict, Any
import logging
import os
from langchain_openai import ChatOpenAI
from agents.distributed.a2a.client import A2AClientManager
from agents.distributed.a2a.messages import TaskRequest, TaskResponse


class ChiefMarketingOfficerAgent:
    """
    Chief Marketing Officer implementation
    
    Responsibilities:
    - Develop go-to-market strategies
    - Build brand awareness
    - Generate demand and leads
    - Analyze market trends
    
    Skills: Marketing strategy, Brand building, Analytics, Communication
    """
    
    def __init__(self, tools: Optional[List] = None):
        self.logger = logging.getLogger(f"executive-team.Chief Marketing Officer")
        self.tools = tools or []
        self.manages_teams = ["marketing-team", "content-team", "brand-team"]
        self.agent = self._create_agent()
        
        # Initialize A2A client for inter-team communication
        self.a2a_client = None
        if self.manages_teams:
            self._init_a2a_client()
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4", temperature=0.7)
        
        return Agent(
            role="Chief Marketing Officer",
            goal="Develop go-to-market strategies Build brand awareness",
            backstory="""You are the CMO of ElfAutomations, responsible for marketing strategy and execution. Within the executive team, you collaborate naturally with other C-suite members. When you need marketing campaigns, content, or brand work executed, you send detailed A2A requests to the marketing team manager, including campaign objectives, target metrics, and deliverable specifications. You develop go-to-market strategies, build brand awareness, and drive demand generation through your subordinate teams.""",
            allow_delegation=False,
            verbose=True,
            tools=self.tools,
            llm=llm
        )
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent
    
    def log_communication(self, message: str, to_agent: Optional[str] = None):
        """Log internal team communications"""
        if to_agent:
            self.logger.info(f"[Chief Marketing Officer → {to_agent}]: {message}")
        else:
            self.logger.info(f"[Chief Marketing Officer]: {message}")
    
    def _init_a2a_client(self):
        """Initialize A2A client for inter-team communication"""
        try:
            self.a2a_client = A2AClientManager()
            self.logger.info(f"A2A client initialized for managing teams: {self.manages_teams}")
        except Exception as e:
            self.logger.error(f"Failed to initialize A2A client: {e}")
            self.a2a_client = None
    
    async def send_task_to_team(self, team_name: str, task_description: str, 
                               success_criteria: List[str], deadline: Optional[str] = None,
                               context: Optional[Dict[str, Any]] = None) -> Optional[TaskResponse]:
        """
        Send a task to a subordinate team via A2A protocol
        
        Args:
            team_name: Name of the team to send the task to
            task_description: Detailed description of the task
            success_criteria: List of criteria that define successful completion
            deadline: Optional deadline for the task
            context: Optional additional context for the task
            
        Returns:
            TaskResponse from the team or None if failed
        """
        if not self.a2a_client:
            self.logger.error("A2A client not initialized")
            return None
            
        if team_name not in self.manages_teams:
            self.logger.error(f"{team_name} is not in managed teams: {self.manages_teams}")
            return None
        
        # Create formal A2A task request
        task_request = TaskRequest(
            from_team="executive-team",
            from_agent="Chief Marketing Officer",
            to_team=team_name,
            task_description=task_description,
            success_criteria=success_criteria,
            deadline=deadline,
            context=context or {},
            priority="normal"
        )
        
        self.logger.info(f"Sending A2A task to {team_name}: {task_description[:100]}")
        
        try:
            response = await self.a2a_client.send_task(team_name, task_request)
            self.logger.info(f"Received response from {team_name}: {response.status}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to send task to {team_name}: {e}")
            return None
    
    async def request_marketing_campaign(self, campaign_type: str, objectives: List[str],
                                       target_metrics: Dict[str, Any], deadline: str) -> Optional[TaskResponse]:
        """
        Request a marketing campaign from the marketing team
        
        Example:
            await cmo.request_marketing_campaign(
                campaign_type="product_launch",
                objectives=["Generate 1000 qualified leads", "Achieve 20% brand awareness increase"],
                target_metrics={"ctr": 2.5, "conversion_rate": 5, "reach": 100000},
                deadline="2024-02-01"
            )
        """
        task_description = f"Execute {campaign_type} marketing campaign with clear deliverables and timelines."
        
        context = {
            "campaign_type": campaign_type,
            "target_metrics": target_metrics,
            "budget_guidelines": "To be confirmed with CFO",
            "brand_guidelines": "Follow latest brand book v2.0"
        }
        
        return await self.send_task_to_team(
            team_name="marketing-team",
            task_description=task_description,
            success_criteria=objectives,
            deadline=deadline,
            context=context
        )
