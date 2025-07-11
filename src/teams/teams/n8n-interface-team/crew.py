#!/usr/bin/env python3
"""
n8n-interface-team Crew Definition
Generated by Team Factory

Purpose: Enable seamless integration between AI teams and n8n automation workflows
Framework: CrewAI
Department: infrastructure
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import Any, Dict, List

from crewai import Crew, Process, Task

# Import team members
from agents import (
    ManagerwithA2AAgent,
    MonitoringSpecialistAgent,
    RegistrySpecialistAgent,
    ResilienceEngineerAgent,
    ValidationSpecialistAgent,
)


class N8NInterfaceTeamCrew:
    """Orchestrates the n8n-interface-team team using CrewAI"""

    def __init__(self):
        self.logger = logging.getLogger("n8n-interface-team.crew")

        # Initialize agents
        self.manager_with_a2a = ManagerwithA2AAgent()
        self.validation_specialist = ValidationSpecialistAgent()
        self.monitoring_specialist = MonitoringSpecialistAgent()
        self.resilience_engineer = ResilienceEngineerAgent()
        self.registry_specialist = RegistrySpecialistAgent()

        # Create the crew
        self.crew = self._create_crew()

    def _create_crew(self) -> Crew:
        """Create and configure the crew"""

        agents = [
            self.manager_with_a2a.agent,
            self.validation_specialist.agent,
            self.monitoring_specialist.agent,
            self.resilience_engineer.agent,
            self.registry_specialist.agent,
        ]

        # Configure process based on team size and structure
        process = Process.hierarchical

        return Crew(
            agents=agents,
            process=process,
            verbose=True,
            memory=True,
            manager_llm=self.manager_with_a2a.llm
            if process == Process.hierarchical
            else None,
            function_calling_llm=self.manager_with_a2a.llm,
        )

    def create_task(self, description: str, context: Dict[str, Any] = None) -> Task:
        """Create a task for the crew"""
        return Task(
            description=description,
            expected_output="A comprehensive response addressing all aspects of the task",
            context=context or {},
        )

    def run(self, task_description: str, context: Dict[str, Any] = None) -> str:
        """Run the crew with a specific task"""
        self.logger.info(f"Starting crew execution: {task_description[:100]}...")

        task = self.create_task(task_description, context)
        result = self.crew.kickoff(inputs={"task": task})

        self.logger.info("Crew execution completed")
        return result

    async def arun(self, task_description: str, context: Dict[str, Any] = None) -> str:
        """Async version of run"""
        # CrewAI doesn't have native async support yet
        # This is a placeholder for future implementation
        return self.run(task_description, context)


# Global instance
_orchestrator_instance = None


def get_orchestrator(tools: Dict[str, List] = None) -> N8NInterfaceTeamCrew:
    """Get or create the team orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = N8NInterfaceTeamCrew()
    return _orchestrator_instance


if __name__ == "__main__":
    # Example usage
    orchestrator = get_orchestrator()

    # Example task
    result = orchestrator.run(
        "Create a comprehensive strategic plan for Q2 2024",
        context={"budget": 100000, "team_size": 5},
    )

    print(result)
