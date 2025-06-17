"""
CrewAI agent generator v2 - using proper template formatting.
"""

from pathlib import Path
from typing import Any, Dict, List

from ...models import TeamMember, TeamSpecification
from ...utils.constants import PERSONALITY_TRAITS
from ..base import BaseGenerator

# Template for CrewAI agent - using format strings instead of f-strings
AGENT_TEMPLATE = '''"""
{role} Agent for {team_name}
"""

{imports}

{conditional_imports}

logger = logging.getLogger(__name__)


def {function_name}(
    llm: Optional[Union[ChatOpenAI, ChatAnthropic]] = None,
    a2a_client: Optional[A2AClient] = None,
    tools: Optional[list] = None,
    enable_evolution: bool = {enable_evolution}
) -> Agent:
    """
    {role} implementation

    Responsibilities:
{responsibilities}

    Skills: {skills}
{extra_info}
    """
    # Create the agent using factory function
    if not llm:
        llm = LLMFactory.create_llm(
            provider="{llm_provider}",
            model="{llm_model}",
            enable_fallback=True
        )

    # Get the enhanced system prompt with personality traits
    backstory = """{backstory}"""
    
    # Load evolved prompt if evolution is enabled
    if enable_evolution:
        try:
            from elf_automations.shared.utils.supabase_client import get_supabase_client
            supabase = get_supabase_client()
            loader = EvolvedAgentLoader(supabase)
            
            # Create base config
            base_config = {{
                "role": "{role}",
                "goal": "{goal}",
                "backstory": backstory,
                "allow_delegation": {allow_delegation},
                "tools": tools or []
            }}
            
            # Load evolved configuration
            evolved_config = loader.load_evolved_agent_config(
                team_id="{team_name}",
                agent_role="{role}",
                base_config=base_config
            )
            
            # Use evolved prompt if available
            if evolved_config and evolved_config.evolved_prompt:
                backstory = evolved_config.evolved_prompt
                logger.info(f"Loaded evolved prompt for {role} (confidence: {{evolved_config.confidence_score}})")
        except Exception as e:
            logger.warning(f"Could not load evolved prompt: {{e}}")

    agent = Agent(
        role="{role}",
        goal="{goal}",
        backstory=backstory,
        allow_delegation={allow_delegation},
        verbose=True,
        tools=tools or [],
        llm=llm
    )

    # Wrap agent with memory and project awareness capabilities
    return MemoryAwareCrewAIAgent(
        agent=agent,
        team_name="{team_name}",
        role="{role}",
        manages_teams={manages_teams},
        a2a_client=a2a_client,
        enable_evolution=enable_evolution,
        enable_conversation_logging={enable_conversation_logging}
    )


class MemoryAwareCrewAIAgent(MemoryAgentMixin, ProjectAwareMixin):
    """Enhanced CrewAI agent with memory and project capabilities."""

    def __init__(self, agent: Agent, team_name: str, role: str,
                 manages_teams: List[str] = None, a2a_client: Optional[A2AClient] = None,
                 enable_evolution: bool = True, enable_conversation_logging: bool = True):
        """Initialize memory-aware agent."""
        # Initialize mixins
        MemoryAgentMixin.__init__(self, team_name=team_name, role=role)
        ProjectAwareMixin.__init__(self)

        self.agent = agent
        self.manages_teams = manages_teams or []
        self.a2a_client = a2a_client
        self.enable_evolution = enable_evolution
        self.enable_conversation_logging = enable_conversation_logging
        
        # Initialize conversation logger if enabled
        if enable_conversation_logging:
            self._conversation_logger = ConversationLogger(team_name)
        else:
            self._conversation_logger = None

        # Initialize A2A if this is a manager
        if manages_teams and a2a_client:
            self._init_a2a_client()

    def execute(self, *args, **kwargs):
        """Execute agent task with memory context."""
        # Start episode in memory
        episode_id = self.start_episode(task=str(args))
        
        # Log task assignment if conversation logging is enabled
        if self._conversation_logger:
            self._conversation_logger.log_message(
                agent_name=self.role,
                message=f"Received task: {{str(args)}}",
                message_type=MessageType.TASK_ASSIGNMENT
            )

        try:
            # Get relevant past experiences
            similar_experiences = self.remember_similar(str(args))
            if similar_experiences:
                logger.info(f"Found {{len(similar_experiences)}} similar past experiences")
                
                # Log that we're using past experiences
                if self._conversation_logger:
                    self._conversation_logger.log_message(
                        agent_name=self.role,
                        message=f"Recalling {{len(similar_experiences)}} similar past experiences",
                        message_type=MessageType.UPDATE
                    )

            # Execute the actual agent
            result = self.agent.execute(*args, **kwargs)
            
            # Log completion
            if self._conversation_logger:
                self._conversation_logger.log_message(
                    agent_name=self.role,
                    message=f"Completed task with result: {{str(result)[:200]}}",
                    message_type=MessageType.TASK_COMPLETION
                )

            # Complete episode with success
            self.complete_episode(episode_id, outcome="success", learnings={{"result": str(result)}})

            return result

        except Exception as e:
            # Log failure
            if self._conversation_logger:
                self._conversation_logger.log_message(
                    agent_name=self.role,
                    message=f"Task failed with error: {{str(e)}}",
                    message_type=MessageType.UPDATE,
                    metadata={{"error": True}}
                )
            
            # Complete episode with failure
            self.complete_episode(episode_id, outcome="failure", learnings={{"error": str(e)}})
            raise

    def __getattr__(self, name):
        """Delegate attribute access to the wrapped agent."""
        return getattr(self.agent, name)
{manager_methods}'''


MANAGER_METHODS_TEMPLATE = '''

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
            return None'''


class CrewAIAgentGenerator(BaseGenerator):
    """Generates CrewAI agent files using proper templates."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """Generate CrewAI agent files."""
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
            agent_content = self._generate_agent_file(member, team_spec)
            filename = self.get_safe_filename(member.name, ".py")

            if self.write_file(agents_dir / filename, agent_content):
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
        """Generate individual agent file using template."""
        function_name = self.get_safe_filename(member.name, "")

        # Get enhanced prompt
        backstory = self._generate_enhanced_prompt(member, team_spec)
        backstory_escaped = (
            backstory.replace('"', '\\"').replace("{", "{{").replace("}", "}}")
        )

        # Generate goal from responsibilities
        goal = (
            ". ".join(member.responsibilities[:2])
            if member.responsibilities
            else f"Excel as {member.role}"
        )

        # Build imports
        imports = [
            "from crewai import Agent",
            "from typing import Optional, Any, Union, List, Dict",
            "from langchain_openai import ChatOpenAI",
            "from langchain_anthropic import ChatAnthropic",
        ]

        # Build conditional imports
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
                "    TeamMemory, LearningSystem, MemoryAgentMixin, with_memory,",
                "    EvolvedAgentLoader",
                ")",
                "from elf_automations.shared.agents import ProjectAwareMixin",
                "from tools.conversation_logging_system import ConversationLogger, MessageType",
                "from datetime import datetime",
                "import logging",
            ]
        )

        # Build responsibilities
        responsibilities = "\n".join(f"    - {r}" for r in member.responsibilities)

        # Build extra info
        extra_info = ""
        if member.personality_traits:
            extra_info += (
                f"\n    Personality Traits: {', '.join(member.personality_traits)}"
            )
        if member.manages_teams:
            extra_info += f"\n    Manages Teams: {', '.join(member.manages_teams)}"

        # Manager methods
        manager_methods = ""
        if member.is_manager or member.manages_teams:
            manager_methods = MANAGER_METHODS_TEMPLATE

        # Format the template
        return AGENT_TEMPLATE.format(
            role=member.role,
            team_name=team_spec.name,
            imports="\n".join(imports),
            conditional_imports="\n".join(conditional_imports),
            function_name=function_name,
            responsibilities=responsibilities,
            skills=", ".join(member.skills),
            extra_info=extra_info,
            llm_provider=team_spec.llm_provider.lower(),
            llm_model=team_spec.llm_model,
            backstory=backstory_escaped,
            goal=goal,
            allow_delegation=str(member.is_manager),
            manages_teams=member.manages_teams,
            manager_methods=manager_methods,
            enable_evolution=str(team_spec.enable_evolution),
            enable_conversation_logging=str(team_spec.enable_conversation_logging),
        )

    def _generate_enhanced_prompt(
        self, member: TeamMember, team_spec: TeamSpecification
    ) -> str:
        """Generate enhanced prompt with personality traits."""
        # If member has a system_prompt (from LLM optimization), use it
        if hasattr(member, 'system_prompt') and member.system_prompt:
            base_prompt = member.system_prompt
            
            # Add project management context if this is a manager and charter exists
            if member.is_manager and team_spec.charter and team_spec.charter.participates_in_multi_team_projects:
                base_prompt += "\n\n" + team_spec.charter.to_manager_addendum()
                
            return base_prompt
        
        # Otherwise, fall back to template-based generation
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
