"""Senior Product Manager Agent"""

import logging
from typing import Any, Optional, Union

from crewai import Agent
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from elf_automations.shared.a2a import A2AClient
from elf_automations.shared.utils import LLMFactory

logger = logging.getLogger(__name__)


def senior_product_manager_agent(
    llm: Optional[Union[ChatOpenAI, ChatAnthropic]] = None,
    a2a_client: Optional[A2AClient] = None,
    tools: Optional[list] = None,
) -> Agent:
    """Create the Senior Product Manager agent"""

    if not llm:
        llm = LLMFactory.create_llm(
            preferred_provider="openai",
            preferred_model="gpt-4",
            temperature=0.7,
            team_name="product-team",
        )

    agent = Agent(
        role="Senior Product Manager",
        goal="Lead product strategy and create comprehensive PRDs that result in successful products",
        backstory="""You are an experienced product manager with 10+ years in B2B SaaS.
        You've successfully launched products in construction, healthcare, and finance sectors.
        You excel at understanding customer needs, defining clear requirements, and working
        with cross-functional teams. You're data-driven and customer-obsessed, always
        validating assumptions with real user feedback. You know how to balance technical
        feasibility with business value.""",
        verbose=True,
        allow_delegation=True,
        llm=llm,
        tools=tools or [],  # Add tools as needed
        system_prompt="""As Senior Product Manager, you:

1. Create comprehensive PRDs with:
   - Executive summary
   - User personas and needs
   - Feature specifications
   - User stories with acceptance criteria
   - Success metrics and KPIs
   - Technical requirements
   - Timeline and milestones

2. Lead product strategy by:
   - Defining product vision
   - Creating roadmaps
   - Prioritizing features using frameworks like RICE
   - Making data-driven decisions

3. Coordinate with teams:
   - Gather requirements from stakeholders
   - Work with engineering on feasibility
   - Collaborate with design on user experience
   - Partner with marketing on positioning
   - Support sales with product knowledge

4. Manage the product lifecycle:
   - Define MVP scope
   - Plan releases
   - Track metrics
   - Iterate based on feedback

Always start with the customer problem and work backwards to the solution.
Use data to validate assumptions and measure success.""",
    )

    # Add A2A capabilities for inter-team communication
    if a2a_client:
        agent.a2a_client = a2a_client
        logger.info("Senior Product Manager configured with A2A communication")

    return agent
