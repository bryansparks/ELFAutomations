#!/usr/bin/env python3
"""
Chief Executive Officer Agent for executive-team
"""

import logging
import os
from typing import Any, Dict, List, Optional

from crewai import Agent
from langchain_openai import ChatOpenAI

from agents.distributed.a2a.client import A2AClientManager
from agents.distributed.a2a.messages import TaskRequest, TaskResponse


class ChiefExecutiveOfficerAgent:
    """
    Chief Executive Officer implementation

    Responsibilities:
    - Set company vision and strategy
    - Make final decisions on major initiatives
    - Coordinate with all department heads
    - Report to board and stakeholders

    Skills: Strategic thinking, Leadership, Decision making, Communication
    """

    def __init__(self, tools: Optional[List] = None):
        self.logger = logging.getLogger(f"executive-team.Chief Executive Officer")
        self.tools = tools or []
        self.manages_teams = ["executive-team"]  # CEO manages through other executives
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
            role="Chief Executive Officer",
            goal="Set company vision and strategy Make final decisions on major initiatives",
            backstory="""You are the CEO of ElfAutomations, responsible for setting the strategic direction of the company. You work with all department heads to ensure alignment and make final decisions on major initiatives. You coordinate with other executives through natural language within your team, but when communicating with subordinate teams, you use formal A2A messages through the executive team's interfaces. You think strategically about market opportunities, competitive positioning, and long-term growth.""",
            allow_delegation=True,  # CEO can delegate in hierarchical crew
            verbose=True,
            tools=self.tools,
            llm=llm,
        )

    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent

    def log_communication(self, message: str, to_agent: Optional[str] = None):
        """Log internal team communications"""
        if to_agent:
            self.logger.info(f"[Chief Executive Officer → {to_agent}]: {message}")
        else:
            self.logger.info(f"[Chief Executive Officer]: {message}")

    def _init_a2a_client(self):
        """Initialize A2A client for inter-team communication"""
        try:
            self.a2a_client = A2AClientManager()
            self.logger.info(
                f"A2A client initialized for managing teams: {self.manages_teams}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize A2A client: {e}")
            self.a2a_client = None

    async def send_strategic_directive(
        self,
        executive_role: str,
        directive: str,
        objectives: List[str],
        deadline: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[TaskResponse]:
        """
        Send a strategic directive to another executive for their team execution

        Since CEO doesn't directly manage operational teams, directives go through
        other executives who then formulate A2A requests to their subordinate teams.

        Args:
            executive_role: The executive to send the directive to (e.g., "Chief Marketing Officer")
            directive: The strategic directive
            objectives: List of objectives to achieve
            deadline: Optional deadline
            context: Optional additional context

        Returns:
            Confirmation or None if failed
        """
        # This would be handled through CrewAI's internal communication
        # The receiving executive would then use their A2A client to communicate with their teams
        self.log_communication(
            f"Strategic directive to {executive_role}: {directive}", executive_role
        )
        return None  # Actual implementation would use CrewAI task delegation
