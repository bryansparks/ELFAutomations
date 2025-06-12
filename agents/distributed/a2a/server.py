"""
A2A Server Implementation for Distributed CrewAI Agents

This module implements the real Google A2A server infrastructure for agent-to-agent communication.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import uvicorn
from a2a.server.agent_execution import AgentExecutor

# Real A2A SDK imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import QueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import TaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Message,
    Part,
    Role,
    Task,
    TextPart,
)

# CrewAI imports
from crewai import Agent, Crew
from crewai import Task as CrewAITask

logger = logging.getLogger(__name__)


class InMemoryTaskStore(TaskStore):
    """
    Simple in-memory implementation of TaskStore for development/testing.
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.logger = logging.getLogger(f"{__name__}.TaskStore")

    async def save(self, task: Task) -> None:
        """Save a task to the store."""
        self.tasks[task.id] = task
        self.logger.debug(f"Saved task {task.id}")

    async def get(self, task_id: str) -> Optional[Task]:
        """Retrieve a task from the store."""
        task = self.tasks.get(task_id)
        if task:
            self.logger.debug(f"Retrieved task {task_id}")
        return task

    async def delete(self, task_id: str) -> bool:
        """Delete a task from the store."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.logger.debug(f"Deleted task {task_id}")
            return True
        return False


class InMemoryQueueManager(QueueManager):
    """
    Simple in-memory implementation of QueueManager for development/testing.
    Manages EventQueue objects for task-based event streaming and buffering.
    """

    def __init__(self):
        from a2a.server.events.event_queue import EventQueue

        self.queues: Dict[str, EventQueue] = {}  # task_id → EventQueue
        self.logger = logging.getLogger(f"{__name__}.QueueManager")

    async def add(self, task_id: str, queue: "EventQueue") -> None:
        """Add a new event queue associated with a task ID."""
        self.queues[task_id] = queue
        self.logger.debug(f"Added EventQueue for task {task_id}")

    async def get(self, task_id: str) -> Optional["EventQueue"]:
        """Retrieve the event queue for a task ID."""
        queue = self.queues.get(task_id)
        if queue:
            self.logger.debug(f"Retrieved EventQueue for task {task_id}")
        return queue

    async def tap(self, task_id: str) -> Optional["EventQueue"]:
        """Create a child event queue (tap) for an existing task ID."""
        if task_id in self.queues:
            child_queue = self.queues[task_id].tap()
            self.logger.debug(f"Created tap EventQueue for task {task_id}")
            return child_queue
        return None

    async def create_or_tap(self, task_id: str) -> "EventQueue":
        """Create a queue if one doesn't exist, otherwise tap the existing one."""
        from a2a.server.events.event_queue import EventQueue

        if task_id not in self.queues:
            # Create new EventQueue for this task
            self.queues[task_id] = EventQueue()
            self.logger.debug(f"Created new EventQueue for task {task_id}")
            return self.queues[task_id]
        else:
            # Return existing queue (could also tap it)
            self.logger.debug(f"Returning existing EventQueue for task {task_id}")
            return self.queues[task_id]

    async def close(self, task_id: str) -> None:
        """Close and remove the event queue for a task ID."""
        if task_id in self.queues:
            queue = self.queues[task_id]
            queue.close()
            del self.queues[task_id]
            self.logger.debug(f"Closed and removed EventQueue for task {task_id}")

    # Legacy methods for backward compatibility (if needed)
    async def enqueue(self, queue_name: str, item: Any) -> None:
        """Add an item to a queue (legacy method)."""
        # This doesn't fit the EventQueue model, but keeping for compatibility
        pass

    async def dequeue(self, queue_name: str) -> Optional[Any]:
        """Remove and return an item from a queue (legacy method)."""
        # This doesn't fit the EventQueue model, but keeping for compatibility
        return None


class CrewAIAgentExecutor(AgentExecutor):
    """
    A2A AgentExecutor implementation that wraps CrewAI agents.

    This class bridges the A2A protocol with CrewAI agent execution.
    """

    def __init__(self, crewai_agent: Agent, agent_id: str):
        """
        Initialize the executor with a CrewAI agent.

        Args:
            crewai_agent: The CrewAI agent to execute tasks
            agent_id: Unique identifier for this agent
        """
        self.crewai_agent = crewai_agent
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self.running_tasks: Dict[str, asyncio.Task] = {}

    async def execute(self, task: Task, context: Dict[str, Any]) -> Message:
        """
        Execute a task using the CrewAI agent (required by AgentExecutor).

        Args:
            task: A2A task object
            context: Execution context

        Returns:
            Message with the execution result
        """
        return await self.execute_task(task, context)

    async def cancel(self, task_id: str) -> bool:
        """
        Cancel a running task (required by AgentExecutor).

        Args:
            task_id: ID of the task to cancel

        Returns:
            True if task was cancelled, False otherwise
        """
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            if not task.done():
                task.cancel()
                del self.running_tasks[task_id]
                self.logger.info(f"Task {task_id} cancelled")
                return True
        return False

    async def execute_task(self, task: Task, context: Dict[str, Any]) -> Message:
        """
        Execute a task using the CrewAI agent.

        Args:
            task: A2A task object
            context: Execution context

        Returns:
            Message with the execution result
        """
        try:
            # Extract task description from task history
            task_description = "Process the given task"
            if task.history:
                for msg in task.history:
                    if msg.parts:
                        for part in msg.parts:
                            if isinstance(part, TextPart):
                                task_description = part.text
                                break
                        if task_description != "Process the given task":
                            break

            self.logger.info(f"Executing task: {task_description}")

            # Create CrewAI task from A2A request
            crewai_task = CrewAITask(
                description=task_description,
                agent=self.crewai_agent,
                expected_output="A comprehensive response to the task",
            )

            # Create a single-agent crew for execution
            crew = Crew(agents=[self.crewai_agent], tasks=[crewai_task], verbose=True)

            # Execute the task
            result = await asyncio.to_thread(crew.kickoff)

            # Create A2A response message
            response = Message(
                kind="message",
                messageId=f"response-{task.id}",
                taskId=task.id,
                contextId=task.contextId,
                role=Role.ASSISTANT,
                parts=[TextPart(text=str(result))],
                metadata={
                    "execution_time": context.get("execution_time", 0),
                    "agent_role": self.crewai_agent.role,
                    "status": "completed",
                },
            )

            self.logger.info(f"Task completed successfully: {task.id}")
            return response

        except Exception as e:
            self.logger.error(f"Task execution failed: {str(e)}")

            # Return error response
            return Message(
                kind="message",
                messageId=f"error-{task.id}",
                taskId=task.id,
                contextId=task.contextId,
                role=Role.ASSISTANT,
                parts=[TextPart(text=f"Error: {str(e)}")],
                metadata={"error": str(e), "status": "failed"},
            )


class A2AServerManager:
    """
    Manages the A2A server lifecycle for distributed agents.

    This class handles server startup, shutdown, and configuration for A2A communication.
    """

    def __init__(
        self,
        agent_card: AgentCard,
        crewai_agent: Agent,
        host: str = "0.0.0.0",
        port: int = 8090,
    ):
        """
        Initialize the A2A server manager.

        Args:
            agent_card: A2A agent card for this agent
            crewai_agent: CrewAI agent to handle tasks
            host: Server host address
            port: Server port
        """
        self.agent_card = agent_card
        self.crewai_agent = crewai_agent
        self.host = host
        self.port = port
        self.logger = logging.getLogger(f"{__name__}.{agent_card.name}")

        # A2A server components
        self.agent_executor: Optional[CrewAIAgentExecutor] = None
        self.task_store: Optional[InMemoryTaskStore] = None
        self.queue_manager: Optional[InMemoryQueueManager] = None
        self.request_handler: Optional[DefaultRequestHandler] = None
        self.app: Optional[A2AStarletteApplication] = None
        self.server: Optional[uvicorn.Server] = None

    async def initialize(self) -> None:
        """Initialize A2A server components."""
        try:
            self.logger.info("Initializing A2A server components...")

            # Initialize agent executor
            self.agent_executor = CrewAIAgentExecutor(
                crewai_agent=self.crewai_agent, agent_id=self.agent_card.name
            )

            # Initialize task store
            self.task_store = InMemoryTaskStore()

            # Initialize queue manager (optional)
            self.queue_manager = InMemoryQueueManager()

            # Initialize request handler
            self.request_handler = DefaultRequestHandler(
                agent_executor=self.agent_executor,
                task_store=self.task_store,
                queue_manager=self.queue_manager,
            )

            # Initialize A2A Starlette application
            self.app = A2AStarletteApplication(
                agent_card=self.agent_card, http_handler=self.request_handler
            )

            self.logger.info("A2A server components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize A2A server: {str(e)}")
            raise

    async def start(self) -> None:
        """Start the A2A server."""
        try:
            if not self.app:
                await self.initialize()

            self.logger.info(f"Starting A2A server on {self.host}:{self.port}")

            # Create uvicorn server configuration
            config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=True,
            )

            self.server = uvicorn.Server(config)

            # Start server in background task
            await self.server.serve()

        except Exception as e:
            self.logger.error(f"Failed to start A2A server: {str(e)}")
            raise

    async def stop(self) -> None:
        """Stop the A2A server."""
        try:
            if self.server:
                self.logger.info("Stopping A2A server...")
                self.server.should_exit = True
                await self.server.shutdown()
                self.logger.info("A2A server stopped")
        except Exception as e:
            self.logger.error(f"Error stopping A2A server: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on A2A server components.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "agent_id": self.agent_card.name,
            "server_running": self.server is not None
            and not getattr(self.server, "should_exit", True),
            "components": {
                "agent_executor": self.agent_executor is not None,
                "task_store": self.task_store is not None,
                "queue_manager": self.queue_manager is not None,
                "request_handler": self.request_handler is not None,
                "app": self.app is not None,
            },
        }


async def create_a2a_server(
    agent_card: AgentCard, crewai_agent: Agent, host: str = "0.0.0.0", port: int = 8090
) -> A2AServerManager:
    """
    Factory function to create and initialize an A2A server.

    Args:
        agent_card: A2A agent card
        crewai_agent: CrewAI agent
        host: Server host
        port: Server port

    Returns:
        Initialized A2AServerManager
    """
    server_manager = A2AServerManager(agent_card, crewai_agent, host, port)
    await server_manager.initialize()
    return server_manager
