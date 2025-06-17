"""
Chief Executive Officer Agent for general-team
"""

from crewai import Agent
from typing import Optional, Any, Union, List, Dict
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from elf_automations.shared.a2a import A2AClient
from elf_automations.shared.a2a.project_messages import (
    TaskAssignment, TaskUpdate, ProjectStatus, ProjectQuery
)
from elf_automations.shared.utils import LLMFactory
from elf_automations.shared.memory import (
    TeamMemory, LearningSystem, MemoryAgentMixin, with_memory
)
from elf_automations.shared.agents import ProjectAwareMixin
from tools.conversation_logging_system import ConversationLogger, MessageType
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def ceo(
    llm: Optional[Union[ChatOpenAI, ChatAnthropic]] = None,
    a2a_client: Optional[A2AClient] = None,
    tools: Optional[list] = None
) -> Agent:
    """
    Chief Executive Officer implementation

    Responsibilities:


    Skills: 

    Personality Traits: visionary
    """
    # Create the agent using factory function
    if not llm:
        llm = LLMFactory.create_llm(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            enable_fallback=True
        )

    # Get the enhanced system prompt with personality traits
    backstory = """You are the Chief Executive Officer for general-team.

Your primary responsibilities include:


You work in the general department.

Personality and work style:"""

    agent = Agent(
        role="Chief Executive Officer",
        goal="Excel as Chief Executive Officer",
        backstory=backstory,
        allow_delegation=True,
        verbose=True,
        tools=tools or [],
        llm=llm
    )

    # Wrap agent with memory and project awareness capabilities
    return MemoryAwareCrewAIAgent(
        agent=agent,
        team_name="general-team",
        role="Chief Executive Officer",
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


    def _init_a2a_client(self):
        """Initialize A2A client for inter-team communication."""
        if self.a2a_client:
            logger.info(f"Initialized A2A client for {{self.role}}")

    def send_task_to_team(self, team_name: str, task: str,
                          context: Dict[str, Any] = None,
                          deadline: Optional[str] = None) -> Optional[str]:
        """
        Send a task to a subordinate team.

        Args:
            team_name: Name of the team to send task to
            task: Task description
            context: Additional context for the task
            deadline: Task deadline

        Returns:
            Task ID if successful
        """
        if not self.a2a_client:
            logger.error("A2A client not initialized")
            return None

        if team_name not in self.manages_teams:
            logger.error(f"Not authorized to send tasks to {{team_name}}")
            return None

        # Create task assignment
        assignment = TaskAssignment(
            task_id=f"{{self.team_name}}_{{datetime.now().strftime('%Y%m%d%H%M%S')}}",
            from_team=self.team_name,
            to_team=team_name,
            title=task,
            description=task,
            context=context or {{}},
            deadline=deadline,
            assigned_by=self.role
        )

        # Log the delegation
        self._conversation_logger.log_message(
            speaker=self.role,
            message=f"Delegating to {{team_name}}: {{task}}",
            message_type=MessageType.DECISION,
            metadata={{"task_id": assignment.task_id, "team": team_name}}
        )

        # Send via A2A
        try:
            response = self.a2a_client.send_task(assignment)
            logger.info(f"Task sent to {{team_name}}: {{assignment.task_id}}")
            return assignment.task_id
        except Exception as e:
            logger.error(f"Failed to send task to {{team_name}}: {{e}}")
            return None

    def check_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Check status of a delegated task."""
        if not self.a2a_client:
            return None

        try:
            status = self.a2a_client.check_status(task_id)
            return status
        except Exception as e:
            logger.error(f"Failed to check task status: {{e}}")
            return None