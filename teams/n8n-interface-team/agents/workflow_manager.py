"""
Manager with A2A Agent for n8n-interface-team
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
    TeamMemory, LearningSystem, MemoryAgentMixin, with_memory,
    EvolvedAgentLoader
)
from elf_automations.shared.agents import ProjectAwareMixin
from tools.conversation_logging_system import ConversationLogger, MessageType
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def workflow_manager(
    llm: Optional[Union[ChatOpenAI, ChatAnthropic]] = None,
    a2a_client: Optional[A2AClient] = None,
    tools: Optional[list] = None,
    enable_evolution: bool = True
) -> Agent:
    """
    Manager with A2A implementation

    Responsibilities:
    - Receives workflow execution requests from other teams via A2A protocol
    - Delegates tasks to appropriate team members based on request type
    - Monitors overall team performance and workflow execution metrics
    - Responds to requesting teams with execution results or error details

    Skills: A2A protocol, workflow orchestration, team management, error handling

    Personality Traits: strategic-thinker
    """
    # Create the agent using factory function
    if not llm:
        llm = LLMFactory.create_llm(
            provider="openai",
            model="gpt-4",
            enable_fallback=True
        )

    # Get the enhanced system prompt with personality traits
    backstory = """You are the Manager with A2A for n8n-interface-team.

Your primary responsibilities include:
- Receives workflow execution requests from other teams via A2A protocol
- Delegates tasks to appropriate team members based on request type
- Monitors overall team performance and workflow execution metrics
- Responds to requesting teams with execution results or error details

You work in the infrastructure department.

Personality and work style:"""
    
    # Load evolved prompt if evolution is enabled
    if enable_evolution:
        try:
            from elf_automations.shared.utils.supabase_client import get_supabase_client
            supabase = get_supabase_client()
            loader = EvolvedAgentLoader(supabase)
            
            # Create base config
            base_config = {
                "role": "Manager with A2A",
                "goal": "Receives workflow execution requests from other teams via A2A protocol. Delegates tasks to appropriate team members based on request type",
                "backstory": backstory,
                "allow_delegation": True,
                "tools": tools or []
            }
            
            # Load evolved configuration
            evolved_config = loader.load_evolved_agent_config(
                team_id="n8n-interface-team",
                agent_role="Manager with A2A",
                base_config=base_config
            )
            
            # Use evolved prompt if available
            if evolved_config and evolved_config.evolved_prompt:
                backstory = evolved_config.evolved_prompt
                logger.info(f"Loaded evolved prompt for Manager with A2A (confidence: {evolved_config.confidence_score})")
        except Exception as e:
            logger.warning(f"Could not load evolved prompt: {e}")

    agent = Agent(
        role="Manager with A2A",
        goal="Receives workflow execution requests from other teams via A2A protocol. Delegates tasks to appropriate team members based on request type",
        backstory=backstory,
        allow_delegation=True,
        verbose=True,
        tools=tools or [],
        llm=llm
    )

    # Wrap agent with memory and project awareness capabilities
    return MemoryAwareCrewAIAgent(
        agent=agent,
        team_name="n8n-interface-team",
        role="Manager with A2A",
        manages_teams=[],
        a2a_client=a2a_client,
        enable_evolution=enable_evolution,
        enable_conversation_logging=True
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
                message=f"Received task: {str(args)}",
                message_type=MessageType.TASK_ASSIGNMENT
            )

        try:
            # Get relevant past experiences
            similar_experiences = self.remember_similar(str(args))
            if similar_experiences:
                logger.info(f"Found {len(similar_experiences)} similar past experiences")
                
                # Log that we're using past experiences
                if self._conversation_logger:
                    self._conversation_logger.log_message(
                        agent_name=self.role,
                        message=f"Recalling {len(similar_experiences)} similar past experiences",
                        message_type=MessageType.UPDATE
                    )

            # Execute the actual agent
            result = self.agent.execute(*args, **kwargs)
            
            # Log completion
            if self._conversation_logger:
                self._conversation_logger.log_message(
                    agent_name=self.role,
                    message=f"Completed task with result: {str(result)[:200]}",
                    message_type=MessageType.TASK_COMPLETION
                )

            # Complete episode with success
            self.complete_episode(episode_id, outcome="success", learnings={"result": str(result)})

            return result

        except Exception as e:
            # Log failure
            if self._conversation_logger:
                self._conversation_logger.log_message(
                    agent_name=self.role,
                    message=f"Task failed with error: {str(e)}",
                    message_type=MessageType.UPDATE,
                    metadata={"error": True}
                )
            
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