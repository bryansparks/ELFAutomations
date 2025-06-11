#!/usr/bin/env python3
"""
Product Team Crew Definition
Built manually due to team_factory.py issues

Purpose: Define product strategy, create PRDs, and ensure product-market fit
Framework: CrewAI
Department: Product
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from crewai import Crew, Process, Task

from elf_automations.shared.a2a import A2AClient
from elf_automations.shared.mcp import MCPClient

# Import ElfAutomations shared modules
from elf_automations.shared.utils import setup_team_logging

# Import all team agents
try:
    # For module execution
    from .agents import (
        business_analyst_agent,
        competitive_intelligence_analyst_agent,
        senior_product_manager_agent,
        technical_product_manager_agent,
        ux_researcher_agent,
    )
except ImportError:
    # For direct execution
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from agents import (
        business_analyst_agent,
        competitive_intelligence_analyst_agent,
        senior_product_manager_agent,
        technical_product_manager_agent,
        ux_researcher_agent,
    )

# Set up logging for natural language communication tracking
logger = setup_team_logging("product-team")


class ProductTeamCrew:
    """
    Orchestrates the product team using CrewAI

    This team creates PRDs, conducts market research, and ensures we build
    products that customers actually want and need.
    """

    def __init__(self, tools: Optional[Dict[str, List]] = None):
        self.logger = logger
        self.tools = tools or {}
        self.agents = self._initialize_agents()
        self.crew = self._create_crew()

    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all team agents with proper tools"""

        # Log natural language communication
        self.logger.info("Product team assembling for new initiative")

        agents = {
            "senior_pm": senior_product_manager_agent(
                tools=self.tools.get("senior_pm", [])
            ),
            "business_analyst": business_analyst_agent(
                tools=self.tools.get("business_analyst", [])
            ),
            "technical_pm": technical_product_manager_agent(
                tools=self.tools.get("technical_pm", [])
            ),
            "ux_researcher": ux_researcher_agent(
                tools=self.tools.get("ux_researcher", [])
            ),
            "competitive_analyst": competitive_intelligence_analyst_agent(
                tools=self.tools.get("competitive_analyst", [])
            ),
        }

        return agents

    def _create_crew(self) -> Crew:
        """Create the CrewAI crew with hierarchical process"""

        # Remove manager from agents list for hierarchical process
        agents = [agent for key, agent in self.agents.items() if key != "senior_pm"]

        return Crew(
            agents=agents,
            tasks=[],  # Tasks will be added dynamically based on request
            process=Process.hierarchical,
            manager_agent=self.agents["senior_pm"],  # Senior PM manages the team
            verbose=True,
        )

    def create_prd(self, product_request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive Product Requirements Document"""

        self.logger.info(
            f"Senior PM received request: {product_request.get('description', 'New product request')}"
        )

        # Define tasks for PRD creation
        tasks = []

        # Task 1: Market Research
        market_research_task = Task(
            description=f"""
            Conduct comprehensive market research for: {product_request.get('description')}

            Include:
            - Target market size and segments
            - Customer pain points and needs
            - Competitive landscape
            - Pricing strategies in the market
            - Regulatory considerations

            Context: {product_request.get('context', {})}
            """,
            agent=self.agents["business_analyst"],
            expected_output="Detailed market research report with data-backed insights",
        )
        tasks.append(market_research_task)

        # Task 2: User Research
        user_research_task = Task(
            description=f"""
            Conduct user research for: {product_request.get('description')}

            Create:
            - User personas based on target segments
            - User journey maps
            - Key jobs-to-be-done
            - Usability requirements
            - Accessibility considerations

            Context: {product_request.get('context', {})}
            """,
            agent=self.agents["ux_researcher"],
            expected_output="User research findings with personas and journey maps",
        )
        tasks.append(user_research_task)

        # Task 3: Technical Feasibility
        technical_analysis_task = Task(
            description=f"""
            Analyze technical requirements for: {product_request.get('description')}

            Define:
            - System architecture approach
            - API requirements
            - Data models
            - Integration needs
            - Performance requirements
            - Security considerations

            Context: {product_request.get('context', {})}
            """,
            agent=self.agents["technical_pm"],
            expected_output="Technical requirements and architecture recommendations",
        )
        tasks.append(technical_analysis_task)

        # Task 4: Competitive Analysis
        competitive_analysis_task = Task(
            description=f"""
            Analyze competitive landscape for: {product_request.get('description')}

            Provide:
            - Direct and indirect competitors
            - Feature comparison matrix
            - Pricing analysis
            - Differentiation opportunities
            - Market positioning recommendations

            Context: {product_request.get('context', {})}
            """,
            agent=self.agents["competitive_analyst"],
            expected_output="Competitive analysis with positioning strategy",
        )
        tasks.append(competitive_analysis_task)

        # Task 5: Create PRD (Senior PM synthesizes everything)
        create_prd_task = Task(
            description=f"""
            Create a comprehensive Product Requirements Document for: {product_request.get('description')}

            Synthesize all research and create:
            1. Executive Summary
            2. Problem Statement
            3. Target Users and Personas
            4. User Stories with Acceptance Criteria
            5. Feature Specifications
            6. Technical Requirements
            7. Success Metrics and KPIs
            8. MVP Scope Definition
            9. Go-to-Market Considerations
            10. Timeline and Milestones

            Use insights from market research, user research, technical analysis, and competitive analysis.

            Context: {product_request.get('context', {})}
            """,
            agent=self.agents["senior_pm"],
            expected_output="Complete PRD ready for engineering team",
        )
        tasks.append(create_prd_task)

        # Update crew with tasks
        self.crew.tasks = tasks

        # Execute the crew
        self.logger.info("Product team beginning PRD creation process")
        result = self.crew.kickoff()

        self.logger.info("PRD creation complete")

        return {"status": "success", "prd": result, "team": "product-team"}

    def execute_task(
        self, task_description: str, context: Dict[str, Any] = None
    ) -> Any:
        """Execute a general product-related task"""

        self.logger.info(f"Product team received task: {task_description}")

        # Create a general task
        task = Task(
            description=task_description,
            agent=self.agents["senior_pm"],  # Senior PM coordinates
            expected_output="Task completion report with deliverables",
        )

        self.crew.tasks = [task]
        result = self.crew.kickoff()

        return result


# Example usage
if __name__ == "__main__":
    # Initialize the crew
    product_crew = ProductTeamCrew()

    # Example: Create a PRD for construction PM platform
    product_request = {
        "description": "Construction project management platform with SMS communication",
        "context": {
            "target_users": "Construction project managers and field workers",
            "key_features": ["SMS messaging", "project dashboard", "offline support"],
            "constraints": ["Non-technical users", "poor connectivity in field"],
            "timeline": "8 weeks to MVP",
        },
    }

    # Create the PRD
    result = product_crew.create_prd(product_request)
    print("PRD Created:", result)
