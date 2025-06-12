"""
Base Agent Classes and Types for ELF Automations

This module provides the foundational classes and types for all AI agents
in the Virtual AI Company Platform.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import structlog

# Removed LangChain imports - using CrewAI instead
# from langchain_anthropic import ChatAnthropic
# from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
# from langgraph.graph import StateGraph
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = structlog.get_logger(__name__)


class AgentType(str, Enum):
    """Types of agents in the organization hierarchy."""

    EXECUTIVE = "executive"
    DEPARTMENT_HEAD = "department_head"
    INDIVIDUAL = "individual"
    SPECIALIST = "specialist"


class AgentStatus(str, Enum):
    """Current status of an agent."""

    INACTIVE = "inactive"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AgentConfig(BaseModel):
    """Configuration for an AI agent."""

    model: str = Field(
        default="claude-3-5-sonnet-20241022", description="LLM model to use"
    )
    max_tokens: int = Field(
        default=4000, ge=100, le=8000, description="Maximum tokens per response"
    )
    temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Model temperature"
    )
    timeout_seconds: int = Field(
        default=60, ge=5, le=300, description="Request timeout"
    )
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum retry attempts"
    )
    tools: List[str] = Field(
        default_factory=list, description="Available tools for this agent"
    )
    department_access: List[str] = Field(
        default_factory=list, description="Departments this agent can access"
    )
    escalation_threshold: int = Field(
        default=3, description="Number of failures before escalation"
    )

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate the model name."""
        allowed_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "gpt-4o",
            "gpt-4o-mini",
        ]
        if v not in allowed_models:
            raise ValueError(f"Model {v} not in allowed models: {allowed_models}")
        return v


class AgentState(BaseModel):
    """Current state of an agent."""

    model_config = ConfigDict(
        extra="forbid", json_encoders={datetime: lambda v: v.isoformat()}
    )

    agent_id: str = Field(description="Unique agent identifier")
    status: AgentStatus = Field(default=AgentStatus.INACTIVE)
    current_task: Optional[str] = Field(default=None, description="Current task ID")
    last_activity: datetime = Field(
        default_factory=datetime.utcnow, description="Last activity timestamp"
    )
    error_count: int = Field(default=0, description="Number of consecutive errors")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional state data"
    )


class AgentMessage(BaseModel):
    """Message structure for inter-agent communication."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Message unique identifier",
    )
    from_agent: str = Field(description="Sender agent ID")
    to_agent: str = Field(description="Recipient agent ID")
    message_type: str = Field(description="Type of message")
    content: Dict[str, Any] = Field(description="Message content")
    priority: int = Field(
        default=3, ge=1, le=5, description="Message priority (1=highest)"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    requires_response: bool = Field(default=False)
    correlation_id: Optional[str] = Field(
        default=None, description="For tracking related messages"
    )


class BaseAgent(ABC):
    """
    Base class for all AI agents in the Virtual AI Company Platform.

    This class provides the foundational functionality that all agents inherit,
    including LLM interaction, state management, and inter-agent communication.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        agent_type: AgentType,
        department: str,
        config: AgentConfig,
        system_prompt: Optional[str] = None,
    ):
        """Initialize the base agent."""
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.department = department
        self.config = config
        self.system_prompt = system_prompt or self._default_system_prompt()

        # Initialize state
        self.state = AgentState(agent_id=agent_id)

        # Initialize LLM
        # COMMENTED OUT - LangChain dependency removed for CrewAI migration
        # self.llm = self._initialize_llm()

        # Initialize logger with agent context
        self.logger = logger.bind(
            agent_id=agent_id,
            agent_name=name,
            agent_type=agent_type.value,
            department=department,
        )

        # Message queue for inter-agent communication
        self._message_queue: asyncio.Queue[AgentMessage] = asyncio.Queue()

        # Task tracking
        self._current_task: Optional[asyncio.Task] = None
        self._task_history: List[Dict[str, Any]] = []

        self.logger.info("Agent initialized", config=config.model_dump())

    # COMMENTED OUT - LangChain dependency removed for CrewAI migration
    # def _initialize_llm(self) -> ChatAnthropic:
    #     """Initialize the language model."""
    #     if self.config.model.startswith("claude"):
    #         return ChatAnthropic(
    #             model=self.config.model,
    #             max_tokens=self.config.max_tokens,
    #             temperature=self.config.temperature,
    #             timeout=self.config.timeout_seconds,
    #         )
    #     else:
    #         # Add support for other models as needed
    #         raise ValueError(f"Unsupported model: {self.config.model}")

    def _default_system_prompt(self) -> str:
        """Generate default system prompt for the agent."""
        return f"""You are {self.name}, an AI agent in the {self.department} department of a virtual AI company.

Your role: {self.agent_type.value}
Department: {self.department}
Agent ID: {self.agent_id}

You are part of an autonomous AI company where agents collaborate to achieve business objectives.
You should:
1. Act professionally and efficiently
2. Collaborate with other agents when needed
3. Escalate complex issues to your supervisor
4. Maintain detailed logs of your actions
5. Follow company policies and procedures

Always respond in a structured format and provide clear reasoning for your decisions."""

    async def send_message(
        self,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any],
        priority: int = 3,
        requires_response: bool = False,
    ) -> str:
        """Send a message to another agent."""
        message = AgentMessage(
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            priority=priority,
            requires_response=requires_response,
        )

        self.logger.info(
            "Sending message",
            to_agent=to_agent,
            message_type=message_type,
            message_id=message.id,
            requires_response=requires_response,
        )

        # In a real implementation, this would use the Agent Gateway
        # For now, we'll implement a simple in-memory message passing
        await self._deliver_message(message)

        return message.id

    async def _deliver_message(self, message: AgentMessage) -> None:
        """Deliver a message to the target agent."""
        # This would be implemented using the Agent Gateway in production
        # For now, we'll use a simple registry-based approach
        from .registry import AgentRegistry

        target_agent = AgentRegistry.get_agent(message.to_agent)
        if target_agent:
            await target_agent._receive_message(message)
        else:
            self.logger.error(
                "Target agent not found", target_agent_id=message.to_agent
            )

    async def _receive_message(self, message: AgentMessage) -> None:
        """Receive a message from another agent."""
        await self._message_queue.put(message)

        self.logger.info(
            "Message received",
            from_agent=message.from_agent,
            message_type=message.message_type,
            message_id=message.id,
        )

    async def process_messages(self) -> None:
        """Process incoming messages."""
        while not self._message_queue.empty():
            try:
                message = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                break
            except Exception as e:
                self.logger.error("Error processing message", error=str(e))

    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle an incoming message."""
        self.logger.info(
            "Processing message",
            message_type=message.message_type,
            from_agent=message.from_agent,
        )

        # Update state
        self.state.last_activity = datetime.utcnow()

        # Route message based on type
        handler_method = f"_handle_{message.message_type}"
        if hasattr(self, handler_method):
            handler = getattr(self, handler_method)
            await handler(message)
        else:
            await self._handle_unknown_message(message)

    async def _handle_unknown_message(self, message: AgentMessage) -> None:
        """Handle unknown message types."""
        self.logger.warning(
            "Unknown message type received",
            message_type=message.message_type,
            from_agent=message.from_agent,
        )

    async def think(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Use the LLM to process a prompt and return a response.

        Args:
            prompt: The prompt to process
            context: Additional context for the prompt

        Returns:
            The LLM response
        """
        try:
            # Build messages
            # messages = [SystemMessage(content=self.system_prompt)]

            # if context:
            #     context_str = f"Context: {context}\n\n"
            #     prompt = context_str + prompt

            # messages.append(HumanMessage(content=prompt))

            # # Get response from LLM
            # self.logger.debug("Sending prompt to LLM", prompt_length=len(prompt))

            # response = await self.llm.ainvoke(messages)

            # self.logger.debug("Received LLM response", response_length=len(response.content))

            # return response.content

            # COMMENTED OUT - LangChain dependency removed for CrewAI migration
            pass

        except Exception as e:
            self.logger.error("Error in LLM interaction", error=str(e))
            self.state.error_count += 1
            raise

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent.

        Args:
            task: Task definition

        Returns:
            Task result
        """
        task_id = task.get("id", str(uuid.uuid4()))

        self.logger.info(
            "Starting task execution", task_id=task_id, task_type=task.get("type")
        )

        # Update state
        self.state.status = AgentStatus.BUSY
        self.state.current_task = task_id
        self.state.last_activity = datetime.utcnow()

        try:
            # Execute the task
            result = await self._execute_task_impl(task)

            # Update state on success
            self.state.status = AgentStatus.ACTIVE
            self.state.current_task = None
            self.state.error_count = 0

            # Log task completion
            self._task_history.append(
                {
                    "task_id": task_id,
                    "task_type": task.get("type"),
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "result": result,
                }
            )

            self.logger.info("Task completed successfully", task_id=task_id)

            return result

        except Exception as e:
            # Update state on error
            self.state.status = AgentStatus.ERROR
            self.state.current_task = None
            self.state.error_count += 1

            # Log task failure
            self._task_history.append(
                {
                    "task_id": task_id,
                    "task_type": task.get("type"),
                    "status": "failed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                }
            )

            self.logger.error("Task execution failed", task_id=task_id, error=str(e))

            # Check if escalation is needed
            if self.state.error_count >= self.config.escalation_threshold:
                await self._escalate_error(task, e)

            raise

    @abstractmethod
    async def _execute_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation-specific task execution logic.

        This method must be implemented by concrete agent classes.
        """
        pass

    async def _escalate_error(self, task: Dict[str, Any], error: Exception) -> None:
        """Escalate an error to a supervisor."""
        self.logger.warning(
            "Escalating error to supervisor",
            error_count=self.state.error_count,
            error=str(error),
        )

        # In a real implementation, this would find and notify the supervisor
        # For now, we'll just log the escalation
        pass

    async def start(self) -> None:
        """Start the agent."""
        self.logger.info("Starting agent")
        self.state.status = AgentStatus.ACTIVE
        self.state.last_activity = datetime.utcnow()

        # Register with the agent registry
        from .registry import AgentRegistry

        AgentRegistry.register_agent(self)

    async def stop(self) -> None:
        """Stop the agent."""
        self.logger.info("Stopping agent")
        self.state.status = AgentStatus.INACTIVE

        # Cancel current task if running
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()

        # Unregister from the agent registry
        from .registry import AgentRegistry

        AgentRegistry.unregister_agent(self.agent_id)

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type.value,
            "department": self.department,
            "status": self.state.status.value,
            "current_task": self.state.current_task,
            "last_activity": self.state.last_activity.isoformat(),
            "error_count": self.state.error_count,
            "message_queue_size": self._message_queue.qsize(),
        }

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id={self.agent_id}, name={self.name}, department={self.department})"
