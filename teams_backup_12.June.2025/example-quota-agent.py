"""
Example agent with quota tracking

Shows how to create agents that automatically track their API usage.
"""

import logging
from typing import Any, Optional, Union

from crewai import Agent
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from elf_automations.shared.a2a import A2AClient
from elf_automations.shared.quota import QuotaManager
from elf_automations.shared.utils import LLMFactory

logger = logging.getLogger(__name__)


def quota_aware_agent(
    role: str,
    goal: str,
    backstory: str,
    team_name: str,
    llm: Optional[Union[ChatOpenAI, ChatAnthropic]] = None,
    a2a_client: Optional[A2AClient] = None,
    tools: Optional[list] = None,
    quota_manager: Optional[QuotaManager] = None,
) -> Agent:
    """
    Create an agent with automatic quota tracking

    This agent will:
    1. Track all LLM usage automatically
    2. Fall back to cheaper models when budget is tight
    3. Report usage statistics
    4. Prevent overspending
    """

    if not llm:
        # Create quota-tracked LLM
        llm = LLMFactory.create_with_quota_tracking(
            team_name=team_name,
            preferred_provider="openai",
            preferred_model="gpt-4",
            temperature=0.7,
            quota_manager=quota_manager,
        )

        logger.info(f"Created quota-tracked LLM for {role}")
        logger.info(
            f"Daily budget: ${llm.quota_manager.get_team_budget(team_name):.2f}"
        )
        logger.info(f"Current balance: ${llm.get_remaining_budget():.2f}")

    # Create agent with quota-tracked LLM
    agent = Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools or [],
        max_iter=5,  # Limit iterations to control costs
        max_execution_time=300,  # 5 minute timeout
        system_prompt=f"""
{backstory}

IMPORTANT: You are part of {team_name} with a daily API budget.
Be concise in your responses to conserve tokens and stay within budget.
If you receive a quota warning, switch to shorter responses.

Your role: {role}
Your goal: {goal}
""",
    )

    # Add quota monitoring capabilities
    if hasattr(llm, "get_usage_report"):
        agent.get_usage_report = lambda: llm.get_usage_report()
        agent.get_remaining_budget = lambda: llm.get_remaining_budget()

    # Add A2A capabilities if provided
    if a2a_client:
        agent.a2a_client = a2a_client
        logger.info(f"{role} configured with A2A communication")

    # Log initial state
    logger.info(f"Agent '{role}' initialized with quota tracking")

    return agent


# Example usage in a team
if __name__ == "__main__":
    import logging
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)

    # Initialize shared quota manager for the team
    quota_path = Path.home() / ".elf_automations" / "quota_data"
    quota_path.mkdir(parents=True, exist_ok=True)
    team_quota_manager = QuotaManager(
        storage_path=quota_path, default_daily_budget=5.0  # $5 per day for the team
    )

    # Create multiple agents sharing the same quota
    agents = []

    # Marketing Manager
    marketing_manager = quota_aware_agent(
        role="Marketing Manager",
        goal="Develop and execute marketing strategies while staying within budget",
        backstory="You are an experienced marketing manager who understands the importance of ROI and budget management.",
        team_name="marketing-team",
        quota_manager=team_quota_manager,
    )
    agents.append(marketing_manager)

    # Content Creator
    content_creator = quota_aware_agent(
        role="Content Creator",
        goal="Create engaging content efficiently",
        backstory="You are a creative content creator who can produce high-quality content concisely.",
        team_name="marketing-team",
        quota_manager=team_quota_manager,
    )
    agents.append(content_creator)

    # Social Media Manager
    social_media_manager = quota_aware_agent(
        role="Social Media Manager",
        goal="Manage social media presence cost-effectively",
        backstory="You are a social media expert who knows how to maximize impact with minimal resources.",
        team_name="marketing-team",
        quota_manager=team_quota_manager,
    )
    agents.append(social_media_manager)

    # Test the agents
    print("\n🧪 Testing Quota-Aware Agents\n")

    for agent in agents:
        print(f"\n📊 {agent.role}:")
        print(f"   Remaining budget: ${agent.get_remaining_budget():.2f}")

        # Simulate task execution
        from crewai import Task

        task = Task(
            description=f"Create a brief marketing plan for a new product launch. Be concise.",
            agent=agent,
            expected_output="Brief marketing plan (2-3 paragraphs)",
        )

        try:
            result = agent.execute_task(task)
            print(f"   ✅ Task completed")
            print(f"   Remaining budget: ${agent.get_remaining_budget():.2f}")

            # Show usage report
            report = agent.get_usage_report()
            today = list(report["days"].values())[0]
            print(f"   Used today: ${today['total_cost']:.4f}")

        except Exception as e:
            print(f"   ❌ Task failed: {e}")

    # Team summary
    print(f"\n📊 Team Summary:")
    print(
        f"   Total budget: ${team_quota_manager.get_team_budget('marketing-team'):.2f}"
    )
    report = team_quota_manager.get_usage_report("marketing-team", days=1)
    print(f"   Total spent: ${report['total_cost']:.4f}")
    print(
        f"   Remaining: ${team_quota_manager.get_team_budget('marketing-team') - report['total_cost']:.2f}"
    )
