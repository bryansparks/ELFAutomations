#!/usr/bin/env python3
"""
Chief Financial Officer Agent for executive-team
"""

import logging
from typing import Any, Dict, List, Optional

from crewai import Agent


class ChiefFinancialOfficerAgent:
    """
    Chief Financial Officer implementation

    Responsibilities:
    - Manage financial planning and analysis
    - Ensure financial health
    - Guide investment decisions
    - Report financial metrics

    Skills: Financial planning, Analysis, Risk management, Strategic thinking
    """

    def __init__(self, tools: Optional[List] = None):
        self.logger = logging.getLogger(f"executive-team.Chief Financial Officer")
        self.tools = tools or []
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        return Agent(
            role="Chief Financial Officer",
            goal="Manage financial planning and analysis Ensure financial health",
            backstory="""You are the CFO of ElfAutomations, responsible for the financial health of the company. You manage budgets, financial planning, and analysis. You guide investment decisions and ensure we maintain strong financial discipline. Provide clear financial insights to support strategic decisions and work with all departments on budget allocation.""",
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
            self.logger.info(f"[Chief Financial Officer → {to_agent}]: {message}")
        else:
            self.logger.info(f"[Chief Financial Officer]: {message}")
