#!/usr/bin/env python3
"""
Chief Operations Officer Agent for executive-team
"""

import logging
from typing import Any, Dict, List, Optional

from crewai import Agent


class ChiefOperationsOfficerAgent:
    """
    Chief Operations Officer implementation

    Responsibilities:
    - Optimize operational efficiency
    - Manage cross-functional processes
    - Ensure smooth daily operations
    - Drive continuous improvement

    Skills: Operations management, Process optimization, Leadership, Analytics
    """

    def __init__(self, tools: Optional[List] = None):
        self.logger = logging.getLogger(f"executive-team.Chief Operations Officer")
        self.tools = tools or []
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        return Agent(
            role="Chief Operations Officer",
            goal="Optimize operational efficiency Manage cross-functional processes",
            backstory="""You are the COO of ElfAutomations, responsible for operational excellence across the company. You optimize processes, ensure smooth daily operations, and drive continuous improvement. You work across all departments to eliminate bottlenecks, improve efficiency, and scale operations. Focus on execution excellence and measurable results.""",
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
            self.logger.info(f"[Chief Operations Officer → {to_agent}]: {message}")
        else:
            self.logger.info(f"[Chief Operations Officer]: {message}")
