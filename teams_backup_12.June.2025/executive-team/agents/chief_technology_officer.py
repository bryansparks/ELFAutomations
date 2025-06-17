#!/usr/bin/env python3
"""
Chief Technology Officer Agent for executive-team
"""

import logging
from typing import Any, Dict, List, Optional

from crewai import Agent


class ChiefTechnologyOfficerAgent:
    """
    Chief Technology Officer implementation

    Responsibilities:
    - Define technical strategy and architecture
    - Oversee product development
    - Manage technical debt and innovation
    - Ensure technical excellence

    Skills: Technical leadership, Architecture, Innovation, Team building
    """

    def __init__(self, tools: Optional[List] = None):
        self.logger = logging.getLogger(f"executive-team.Chief Technology Officer")
        self.tools = tools or []
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        return Agent(
            role="Chief Technology Officer",
            goal="Define technical strategy and architecture Oversee product development",
            backstory="""You are the CTO of ElfAutomations, responsible for all technical aspects of the company. You define technical strategy, oversee product development, and ensure we maintain technical excellence. You balance innovation with stability, and make decisions about technology choices, architecture, and technical investments. Work closely with engineering teams and other executives.""",
            allow_delegation=False,
            verbose=True,
            tools=self.tools,
        )

    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent

    def log_communication(self, message: str, to_agent: Optional[str] = None):
        """Log internal team communications"""
        if to_agent:
            self.logger.info(f"[Chief Technology Officer → {to_agent}]: {message}")
        else:
            self.logger.info(f"[Chief Technology Officer]: {message}")
