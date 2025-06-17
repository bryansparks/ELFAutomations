"""
Chief Financial Officer Agent for general-team
"""

from crewai import Agent
from typing import Optional, Any, Union, List, Dict
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from elf_automations.shared.utils import LLMFactory
from elf_automations.shared.memory import (
    TeamMemory, LearningSystem, MemoryAgentMixin, with_memory
)
from elf_automations.shared.agents import ProjectAwareMixin
from tools.conversation_logging_system import ConversationLogger, MessageType
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def cfo(
    llm: Optional[Union[ChatOpenAI, ChatAnthropic]] = None,
    a2a_client: Optional[A2AClient] = None,
    tools: Optional[list] = None
) -> Agent:
    """
    Chief Financial Officer implementation

    Responsibilities:


    Skills: 

    Personality Traits: detail_oriented
    """
    # Create the agent using factory function
    if not llm:
        llm = LLMFactory.create_llm(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            enable_fallback=True
        )

    # Get the enhanced system prompt with personality traits
    backstory = """You are the Chief Financial Officer for general-team.

Your primary responsibilities include:


You work in the general department.

Personality and work style:"""

    agent = Agent(
        role="Chief Financial Officer",
        goal="Excel as Chief Financial Officer",
        backstory=backstory,
        allow_delegation=False,
        verbose=True,
        tools=tools or [],
        llm=llm
    )

    # Wrap agent with memory and project awareness capabilities
    return MemoryAwareCrewAIAgent(
        agent=agent,
        team_name="general-team",
        role="Chief Financial Officer",
        manages_teams=[],
        a2a_client=a2a_client
    )


class MemoryAwareCrewAIAgent(MemoryAgentMixin, ProjectAwareMixin):
    """Enhanced CrewAI agent with memory and project capabilities."""

    def __init__(self, agent: Agent, team_name: str, role: str,
                 manages_teams: List[str] = None, a2a_client: Optional[A2AClient] = None):
        """Initialize memory-aware agent."""
        # Initialize mixins
        MemoryAgentMixin.__init__(self, team_name=team_name, role=role)
        ProjectAwareMixin.__init__(self)

        self.agent = agent
        self.manages_teams = manages_teams or []
        self.a2a_client = a2a_client
        self._conversation_logger = ConversationLogger(team_name)

        # Initialize A2A if this is a manager
        if manages_teams and a2a_client:
            self._init_a2a_client()

    def execute(self, *args, **kwargs):
        """Execute agent task with memory context."""
        # Start episode in memory
        episode_id = self.start_episode(task=str(args))

        try:
            # Get relevant past experiences
            similar_experiences = self.remember_similar(str(args))
            if similar_experiences:
                logger.info(f"Found {len(similar_experiences)} similar past experiences")

            # Execute the actual agent
            result = self.agent.execute(*args, **kwargs)

            # Complete episode with success
            self.complete_episode(episode_id, outcome="success", learnings={"result": str(result)})

            return result

        except Exception as e:
            # Complete episode with failure
            self.complete_episode(episode_id, outcome="failure", learnings={"error": str(e)})
            raise

    def __getattr__(self, name):
        """Delegate attribute access to the wrapped agent."""
        return getattr(self.agent, name)
