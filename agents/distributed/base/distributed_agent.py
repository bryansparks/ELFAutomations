"""
Base DistributedCrewAIAgent class that integrates CrewAI with Google A2A protocol
for distributed agent deployment in Kubernetes.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import structlog
from crewai import Agent, Crew, Task
from pydantic import BaseModel, Field

# Setup logger first
logger = structlog.get_logger(__name__)

from a2a.client import A2AClient
from a2a.server.apps import A2AStarletteApplication

# Real A2A SDK imports - REQUIRED, no fallback
from a2a.types import AgentCapabilities, AgentCard, AgentSkill, Message

from ..a2a.server import A2AServerManager, create_a2a_server

logger.info("✅ Using real Google A2A SDK (official version)")
A2AMessage = Message  # Alias for compatibility

import os

# Import health checks and lifecycle with absolute imports
import sys

base_path = os.path.dirname(__file__)
if base_path not in sys.path:
    sys.path.insert(0, base_path)

from health_checks import HealthCheckMixin
from lifecycle import AgentLifecycleMixin

# TODO: Fix these imports when we implement the full A2A integration
# from ..a2a.client import A2AClientManager
# from ..a2a.messages import A2AMessage, MessageType
# from ..a2a.discovery import DiscoveryService


class AgentConfig(BaseModel):
    """Configuration for a distributed CrewAI agent."""

    agent_id: str = Field(..., description="Unique identifier for this agent")
    role: str = Field(..., description="Role/job title of the agent")
    goal: str = Field(..., description="Primary goal of the agent")
    backstory: str = Field(..., description="Background story for the agent")
    department: str = Field(..., description="Department this agent belongs to")

    # A2A Configuration
    a2a_host: str = Field(default="0.0.0.0", description="Host for A2A server")
    a2a_port: int = Field(default=8080, description="Port for A2A server")
    discovery_endpoint: Optional[str] = Field(
        default=None, description="A2A discovery service endpoint"
    )

    # Kubernetes Configuration
    namespace: str = Field(
        default="elf-automations", description="Kubernetes namespace"
    )
    service_name: Optional[str] = Field(
        default=None, description="Kubernetes service name"
    )

    # Scaling Configuration
    min_replicas: int = Field(default=1, description="Minimum number of replicas")
    max_replicas: int = Field(default=10, description="Maximum number of replicas")
    target_cpu_utilization: int = Field(
        default=70, description="Target CPU utilization for scaling"
    )


class DistributedCrewAIAgent(HealthCheckMixin, AgentLifecycleMixin):
    """
    Base class for distributed CrewAI agents that communicate via A2A protocol
    and deploy as individual Kubernetes services.
    """

    def __init__(self, config: AgentConfig):
        """Initialize the distributed CrewAI agent."""
        self.config = config
        self.logger = structlog.get_logger(f"agent.{config.agent_id}")

        # Initialize mixins
        HealthCheckMixin.__init__(self)
        AgentLifecycleMixin.__init__(self)

        # CrewAI Agent
        self.crewai_agent = Agent(
            role=config.role,
            goal=config.goal,
            backstory=config.backstory,
            verbose=True,
            allow_delegation=True,
            memory=True,
        )

        # A2A components
        self.a2a_client: Optional[A2AClient] = None
        self.a2a_server_manager: Optional[A2AServerManager] = None

        # Health and lifecycle
        self.is_running = False
        self.health_status = "initializing"
        self.start_time: Optional[datetime] = None

        # Initialize metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "uptime_start": None,
        }

        self.logger.info("✅ Using real Google A2A SDK (official version)")

        # Agent state
        self.tasks_completed = 0
        self.messages_sent = 0
        self.messages_received = 0

        self.logger.info(f"Initialized distributed agent: {config.agent_id}")

    async def start(self) -> None:
        """Start the distributed agent."""
        try:
            self.logger.info(f"Starting agent {self.config.agent_id}")

            # Start lifecycle
            await self.start_lifecycle()

            # Create and start A2A server
            await self._start_a2a_server()

            # Register with discovery service
            await self._register_with_discovery()

            # Start health checks
            self.start_health_checks()

            self.is_running = True
            self.start_time = datetime.utcnow()

            self.logger.info(f"Agent {self.config.agent_id} started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start agent {self.config.agent_id}: {e}")
            raise

    async def stop(self) -> None:
        """Stop the distributed agent."""
        try:
            self.logger.info(f"Stopping agent {self.config.agent_id}")

            self.is_running = False

            # Stop health checks
            self.stop_health_checks()

            # Unregister from discovery
            await self._unregister_from_discovery()

            # Stop A2A server
            if self.a2a_server:
                await self.a2a_server.stop()

            # Stop lifecycle
            await self.stop_lifecycle()

            self.logger.info(f"Agent {self.config.agent_id} stopped successfully")

        except Exception as e:
            self.logger.error(f"Failed to stop agent {self.config.agent_id}: {e}")
            raise

    async def execute_task(
        self, task_description: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a task using the CrewAI agent."""
        try:
            self.logger.info(f"Executing task: {task_description}")

            # Create CrewAI task
            task = Task(
                description=task_description,
                agent=self.crewai_agent,
                expected_output="Detailed task completion report",
            )

            # Create crew with single agent and task
            crew = Crew(agents=[self.crewai_agent], tasks=[task], verbose=True)

            # Execute the task
            result = crew.kickoff()

            self.tasks_completed += 1

            self.logger.info(f"Task completed successfully")

            return {
                "status": "completed",
                "result": str(result),
                "task_id": str(uuid.uuid4()),
                "agent_id": self.config.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "context": context or {},
            }

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "task_id": str(uuid.uuid4()),
                "agent_id": self.config.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def send_message(
        self, target_agent_id: str, message: A2AMessage
    ) -> Dict[str, Any]:
        """Send a message to another agent via A2A protocol."""
        try:
            self.logger.info(
                f"Sending message to {target_agent_id}: {message.message_type}"
            )

            # Send via A2A client manager
            response = await self.a2a_client_manager.send_message(
                target_agent_id, message
            )

            self.messages_sent += 1

            return response

        except Exception as e:
            self.logger.error(f"Failed to send message to {target_agent_id}: {e}")
            raise

    async def handle_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming A2A message. Override in subclasses."""
        self.logger.info(
            f"Received message from {message.from_agent}: {message.message_type}"
        )

        self.messages_received += 1

        # Default implementation - echo back
        return {
            "status": "received",
            "message": f"Agent {self.config.agent_id} received message",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_agent_card(self) -> AgentCard:
        """Generate A2A agent card for discovery."""
        capabilities = AgentCapabilities(
            pushNotifications=True, stateTransitionHistory=True, streaming=False
        )

        return AgentCard(
            agent_id=self.config.agent_id,
            name=f"{self.config.role} ({self.config.agent_id})",
            description=f"{self.config.backstory[:200]}..."
            if len(self.config.backstory) > 200
            else self.config.backstory,
            version="1.0.0",
            url=f"http://{self.config.a2a_host}:{self.config.a2a_port}",
            capabilities=capabilities,
            defaultInputModes=["text", "json"],
            defaultOutputModes=["text", "json"],
            skills=[
                AgentSkill(
                    id="task_execution",
                    name="task_execution",
                    description="Execute CrewAI tasks and workflows",
                    inputModes=["text", "json"],
                    outputModes=["text", "json"],
                    tags=["crewai", "task", "execution"],
                    examples=[],
                ),
                AgentSkill(
                    id="a2a_communication",
                    name="a2a_communication",
                    description="Communicate with other agents via A2A protocol",
                    inputModes=["text", "json"],
                    outputModes=["text", "json"],
                    tags=["a2a", "communication", "protocol"],
                    examples=[],
                ),
                AgentSkill(
                    id="collaboration",
                    name="collaboration",
                    description="Collaborate on multi-agent workflows",
                    inputModes=["text", "json"],
                    outputModes=["text", "json"],
                    tags=["collaboration", "workflow", "multi-agent"],
                    examples=[],
                ),
            ],
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics for monitoring."""
        uptime = None
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "agent_id": self.config.agent_id,
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "tasks_completed": self.tasks_completed,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "health_status": self.get_health_status(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _start_a2a_server(self) -> None:
        """Start the A2A server for receiving messages."""
        try:
            self.logger.info(
                f"Starting A2A server on {self.config.a2a_host}:{self.config.a2a_port}"
            )

            # Generate agent card for A2A server
            agent_card = self.get_agent_card()

            # Create and start A2A server
            self.a2a_server_manager = await create_a2a_server(
                agent_card=agent_card,
                crewai_agent=self.crewai_agent,
                host=self.config.a2a_host,
                port=self.config.a2a_port,
            )

            # Start server in background task
            asyncio.create_task(self.a2a_server_manager.start())

            # Wait a moment for server to start
            await asyncio.sleep(1)

            self.logger.info("Real A2A server started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start A2A server: {str(e)}")
            raise

    async def _register_with_discovery(self) -> None:
        """Register this agent with the A2A discovery service."""
        self.logger.info("Real A2A discovery registration not yet implemented")

    async def _unregister_from_discovery(self) -> None:
        """Unregister this agent from the A2A discovery service."""
        self.logger.info("Real A2A discovery unregistration not yet implemented")
