"""
CrewAI agent generator.
"""

from pathlib import Path
from typing import Any, Dict, List

from ...models import TeamMember, TeamSpecification
from ...utils.constants import PERSONALITY_TRAITS
from ..base import BaseGenerator


class CrewAIAgentGenerator(BaseGenerator):
    """Generates CrewAI agent files."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate CrewAI agent files.

        Args:
            team_spec: Team specification

        Returns:
            Generation results
        """
        results = {"generated_files": [], "errors": []}

        # Create agents directory
        team_dir = self.get_team_directory(team_spec)
        agents_dir = self.ensure_directory(team_dir / "agents")

        # Generate __init__.py
        init_content = self._generate_init_file(team_spec)
        if self.write_file(agents_dir / "__init__.py", init_content):
            results["generated_files"].append("agents/__init__.py")

        # Generate each agent file
        for member in team_spec.members:
            agent_file = self._generate_agent_file(member, team_spec)
            filename = self.get_safe_filename(member.name, ".py")

            if self.write_file(agents_dir / filename, agent_file):
                results["generated_files"].append(f"agents/{filename}")
            else:
                results["errors"].append(f"Failed to generate agent: {member.name}")

        return results

    def _generate_init_file(self, team_spec: TeamSpecification) -> str:
        """Generate __init__.py for agents module."""
        imports = []

        for member in team_spec.members:
            function_name = self.get_safe_filename(member.name, "")
            module_name = self.get_safe_filename(member.name, "")
            imports.append(f"from .{module_name} import {function_name}")

        all_exports = [self.get_safe_filename(m.name, "") for m in team_spec.members]

        return f'''"""
{team_spec.name} Agents

This module contains all agent implementations for the {team_spec.name}.
"""

{chr(10).join(imports)}

__all__ = {all_exports}
'''

    def _generate_agent_file(
        self, member: TeamMember, team_spec: TeamSpecification
    ) -> str:
        """Generate individual agent file."""
        function_name = self.get_safe_filename(member.name, "")

        # Get enhanced prompt
        enhanced_prompt = self._generate_enhanced_prompt(member, team_spec)
        enhanced_prompt_escaped = enhanced_prompt.replace('"', '\\"')

        # Generate goal from responsibilities
        goal = (
            ". ".join(member.responsibilities[:2])
            if member.responsibilities
            else f"Excel as {member.role}"
        )

        # Base imports
        imports = [
            "from crewai import Agent",
            "from typing import Optional, Any, Union, List, Dict",
            "from langchain_openai import ChatOpenAI",
            "from langchain_anthropic import ChatAnthropic",
        ]

        # Add conditional imports
        conditional_imports = []
        if member.has_a2a_capabilities():
            conditional_imports.extend(
                [
                    "from elf_automations.shared.a2a import A2AClient",
                    "from elf_automations.shared.a2a.project_messages import (",
                    "    TaskAssignment, TaskUpdate, ProjectStatus, ProjectQuery",
                    ")",
                ]
            )

        conditional_imports.extend(
            [
                "from elf_automations.shared.utils import LLMFactory",
                "from elf_automations.shared.memory import (",
                "    TeamMemory, LearningSystem, MemoryAgentMixin, with_memory",
                ")",
                "from elf_automations.shared.agents import ProjectAwareMixin",
                "from tools.conversation_logging_system import ConversationLogger, MessageType",
                "from datetime import datetime",
                "import logging",
            ]
        )

        # Build agent content
        content = f'''"""
{member.role} Agent for {team_spec.name}
"""

{chr(10).join(imports)}

{chr(10).join(conditional_imports)}

logger = logging.getLogger(__name__)


def {function_name}(
    llm: Optional[Union[ChatOpenAI, ChatAnthropic]] = None,
    a2a_client: Optional[A2AClient] = None,
    tools: Optional[list] = None
) -> Agent:
    """
    {member.role} implementation

    Responsibilities:
{chr(10).join(f"    - {r}" for r in member.responsibilities)}

    Skills: {', '.join(member.skills)}
    '''

        # Add personality traits if any
        if member.personality_traits:
            content += f"""    Personality Traits: {', '.join(member.personality_traits)}
    """

        # Add management info if manager
        if member.manages_teams:
            content += f"""    Manages Teams: {', '.join(member.manages_teams)}
    """

        content += f'''    """
    # Create the agent using factory function
    if not llm:
        llm = LLMFactory.create_llm(
            provider="{team_spec.llm_provider.lower()}",
            model="{team_spec.llm_model}",
            enable_fallback=True
        )

    # Get the enhanced system prompt with personality traits
    backstory = """{enhanced_prompt_escaped}"""

    agent = Agent(
        role="{member.role}",
        goal="{goal}",
        backstory=backstory,
        allow_delegation={str(member.is_manager)},
        verbose=True,
        tools=tools or [],
        llm=llm
    )

    # Wrap agent with memory and project awareness capabilities
    return MemoryAwareCrewAIAgent(
        agent=agent,
        team_name="{team_spec.name}",
        role="{member.role}",
        manages_teams={member.manages_teams},
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
'''

        # Add manager-specific methods if needed
        if member.is_manager or member.manages_teams:
            content += self._generate_manager_methods(member, team_spec)

        return content

    def _generate_enhanced_prompt(
        self, member: TeamMember, team_spec: TeamSpecification
    ) -> str:
        """Generate enhanced prompt with personality traits."""
        base_prompt = f"""You are the {member.role} for {team_spec.name}.

Your primary responsibilities include:
{chr(10).join(f"- {r}" for r in member.responsibilities)}

You work in the {team_spec.department} department"""

        if team_spec.reporting_to:
            base_prompt += f" reporting to the {team_spec.reporting_to}"

        base_prompt += "."

        # Add personality modifiers
        if member.personality_traits:
            base_prompt += "\n\nPersonality and work style:"

            for trait in member.personality_traits:
                if trait in PERSONALITY_TRAITS:
                    modifiers = PERSONALITY_TRAITS[trait]["modifiers"]
                    base_prompt += f"\n{chr(10).join(modifiers)}"

        # Add collaboration note
        if member.communicates_with:
            base_prompt += f"\n\nYou regularly collaborate with: {', '.join(member.communicates_with)}"

        return base_prompt

    def _generate_manager_methods(
        self, member: TeamMember, team_spec: TeamSpecification
    ) -> str:
        """Generate manager-specific A2A methods."""
        return '''

    def _init_a2a_client(self):
        """Initialize A2A client for inter-team communication."""
        if self.a2a_client:
            logger.info(f"Initialized A2A client for {self.role}")

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
            logger.error(f"Not authorized to send tasks to {team_name}")
            return None

        # Create task assignment
        assignment = TaskAssignment(
            task_id=f"{self.team_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            from_team=self.team_name,
            to_team=team_name,
            title=task,
            description=task,
            context=context or {},
            deadline=deadline,
            assigned_by=self.role
        )

        # Log the delegation
        self._conversation_logger.log_message(
            speaker=self.role,
            message=f"Delegating to {team_name}: {task}",
            message_type=MessageType.DECISION,
            metadata={"task_id": assignment.task_id, "team": team_name}
        )

        # Send via A2A
        try:
            response = self.a2a_client.send_task(assignment)
            logger.info(f"Task sent to {team_name}: {assignment.task_id}")
            return assignment.task_id
        except Exception as e:
            logger.error(f"Failed to send task to {team_name}: {e}")
            return None

    def check_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Check status of a delegated task."""
        if not self.a2a_client:
            return None

        try:
            status = self.a2a_client.check_status(task_id)
            return status
        except Exception as e:
            logger.error(f"Failed to check task status: {e}")
            return None
'''
