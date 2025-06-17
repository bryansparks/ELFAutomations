"""
Resilience Engineer Agent for n8n-interface-team
"""

from crewai import Agent
from typing import Optional, Any, Union, List, Dict
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

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


def error_handler(
    llm: Optional[Union[ChatOpenAI, ChatAnthropic]] = None,
    a2a_client: Optional[A2AClient] = None,
    tools: Optional[list] = None,
    enable_evolution: bool = True
) -> Agent:
    """
    Resilience Engineer implementation

    Responsibilities:
    - Manages workflow execution failures and implements retry logic
    - Categorizes errors and determines appropriate recovery strategies
    - Maintains error logs and patterns for continuous improvement
    - Coordinates with n8n team for persistent issues

    Skills: error handling, retry strategies, logging, pattern recognition

    Personality Traits: problem-solver
    """
    # Create the agent using factory function
    if not llm:
        llm = LLMFactory.create_llm(
            provider="openai",
            model="gpt-4",
            enable_fallback=True
        )

    # Get the enhanced system prompt with personality traits
    backstory = """You are the Resilience Engineer for n8n-interface-team.

Your primary responsibilities include:
- Manages workflow execution failures and implements retry logic
- Categorizes errors and determines appropriate recovery strategies
- Maintains error logs and patterns for continuous improvement
- Coordinates with n8n team for persistent issues

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
                "role": "Resilience Engineer",
                "goal": "Manages workflow execution failures and implements retry logic. Categorizes errors and determines appropriate recovery strategies",
                "backstory": backstory,
                "allow_delegation": False,
                "tools": tools or []
            }
            
            # Load evolved configuration
            evolved_config = loader.load_evolved_agent_config(
                team_id="n8n-interface-team",
                agent_role="Resilience Engineer",
                base_config=base_config
            )
            
            # Use evolved prompt if available
            if evolved_config and evolved_config.evolved_prompt:
                backstory = evolved_config.evolved_prompt
                logger.info(f"Loaded evolved prompt for Resilience Engineer (confidence: {evolved_config.confidence_score})")
        except Exception as e:
            logger.warning(f"Could not load evolved prompt: {e}")

    agent = Agent(
        role="Resilience Engineer",
        goal="Manages workflow execution failures and implements retry logic. Categorizes errors and determines appropriate recovery strategies",
        backstory=backstory,
        allow_delegation=False,
        verbose=True,
        tools=tools or [],
        llm=llm
    )

    # Wrap agent with memory and project awareness capabilities
    return MemoryAwareCrewAIAgent(
        agent=agent,
        team_name="n8n-interface-team",
        role="Resilience Engineer",
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
