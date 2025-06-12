"""
A2A client manager for handling agent-to-agent communication.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

# Real A2A SDK imports - REQUIRED, no fallback
from a2a.client import A2AClient
from a2a.types import AgentCard

from .discovery import DiscoveryService
from .messages import A2AMessage, MessageType, create_message


class A2AClientManager:
    """
    Manages A2A client connections and message routing for distributed agents.
    """

    def __init__(
        self,
        agent_id: str,
        discovery_endpoint: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize the A2A client manager."""
        self.agent_id = agent_id
        self.discovery_endpoint = discovery_endpoint
        self.timeout = timeout
        self.max_retries = max_retries

        # Client connections cache
        self.clients: Dict[str, A2AClient] = {}
        self.client_cache_ttl = 300  # 5 minutes
        self.client_last_used: Dict[str, datetime] = {}

        # Discovery service
        self.discovery = (
            DiscoveryService(discovery_endpoint) if discovery_endpoint else None
        )

        # Message tracking
        self.pending_messages: Dict[str, A2AMessage] = {}
        self.message_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000

        # Health check
        self.last_health_check: Optional[datetime] = None
        self.health_check_interval = 60  # seconds

        self.logger = logging.getLogger(f"a2a_client.{agent_id}")
        self.logger.info(f"A2A client manager initialized for agent: {agent_id}")

    async def send_message(
        self, target_agent_id: str, message: A2AMessage
    ) -> Dict[str, Any]:
        """Send a message to another agent."""
        try:
            self.logger.info(
                f"Sending {message.message_type.value} message to {target_agent_id}"
            )

            # Get or create client for target agent
            client = await self._get_client(target_agent_id)

            if not client:
                raise Exception(
                    f"Could not establish connection to agent: {target_agent_id}"
                )

            # Convert message to A2A format
            a2a_payload = self._message_to_a2a_payload(message)

            # Send message with retries
            response = await self._send_with_retries(client, a2a_payload, message)

            # Record message in history
            self._record_message(message, response, "sent")

            return response

        except Exception as e:
            self.logger.error(f"Failed to send message to {target_agent_id}: {e}")
            self._record_message(message, {"error": str(e)}, "failed")
            raise

    async def broadcast_message(
        self, message: A2AMessage, target_agents: List[str]
    ) -> Dict[str, Any]:
        """Broadcast a message to multiple agents."""
        results = {}

        for target_agent_id in target_agents:
            try:
                # Create a copy of the message for each target
                agent_message = message.copy()
                agent_message.to_agent = target_agent_id

                result = await self.send_message(target_agent_id, agent_message)
                results[target_agent_id] = result

            except Exception as e:
                self.logger.error(
                    f"Failed to send broadcast message to {target_agent_id}: {e}"
                )
                results[target_agent_id] = {"error": str(e)}

        return results

    async def register_agent(self, agent_card: AgentCard) -> bool:
        """Register this agent with the discovery service."""
        if not self.discovery:
            self.logger.warning("No discovery service configured")
            return False

        try:
            await self.discovery.register_agent(agent_card)
            self.logger.info(f"Agent {self.agent_id} registered with discovery service")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register agent with discovery: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the discovery service."""
        if not self.discovery:
            return False

        try:
            await self.discovery.unregister_agent(agent_id)
            self.logger.info(f"Agent {agent_id} unregistered from discovery service")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister agent from discovery: {e}")
            return False

    async def discover_agents(
        self, capabilities: Optional[List[str]] = None
    ) -> List[AgentCard]:
        """Discover available agents."""
        if not self.discovery:
            self.logger.warning("No discovery service configured")
            return []

        try:
            agents = await self.discovery.discover_agents(capabilities)
            self.logger.info(f"Discovered {len(agents)} agents")
            return agents

        except Exception as e:
            self.logger.error(f"Failed to discover agents: {e}")
            return []

    async def health_check(self) -> bool:
        """Perform health check on A2A communication."""
        try:
            # Check if discovery service is reachable
            if self.discovery:
                discovery_healthy = await self.discovery.health_check()
                if not discovery_healthy:
                    return False

            # Clean up stale client connections
            await self._cleanup_stale_clients()

            self.last_health_check = datetime.utcnow()
            return True

        except Exception as e:
            self.logger.error(f"A2A health check failed: {e}")
            return False

    async def _get_client(self, target_agent_id: str) -> Optional[A2AClient]:
        """Get or create an A2A client for the target agent."""
        try:
            # Check if we have a cached client
            if target_agent_id in self.clients:
                # Check if client is still valid
                last_used = self.client_last_used.get(target_agent_id)
                if (
                    last_used
                    and (datetime.utcnow() - last_used).seconds < self.client_cache_ttl
                ):
                    self.client_last_used[target_agent_id] = datetime.utcnow()
                    return self.clients[target_agent_id]
                else:
                    # Remove stale client
                    del self.clients[target_agent_id]
                    if target_agent_id in self.client_last_used:
                        del self.client_last_used[target_agent_id]

            # Discover target agent
            if self.discovery:
                agent_card = await self.discovery.get_agent(target_agent_id)
                if not agent_card:
                    self.logger.error(
                        f"Agent {target_agent_id} not found in discovery service"
                    )
                    return None

                # Create new client
                endpoint = agent_card.endpoints.get("a2a")
                if not endpoint:
                    self.logger.error(
                        f"No A2A endpoint found for agent {target_agent_id}"
                    )
                    return None

                client = A2AClient(endpoint=endpoint, timeout=self.timeout)

                # Cache the client
                self.clients[target_agent_id] = client
                self.client_last_used[target_agent_id] = datetime.utcnow()

                return client
            else:
                # No discovery service - try direct connection
                # This would require some other mechanism to know the endpoint
                self.logger.warning(
                    f"No discovery service available for agent {target_agent_id}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Failed to get client for {target_agent_id}: {e}")
            return None

    async def _send_with_retries(
        self, client: A2AClient, payload: Dict[str, Any], message: A2AMessage
    ) -> Dict[str, Any]:
        """Send message with retry logic."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # For now, we'll simulate the A2A client call
                # In a real implementation, this would use the actual A2A SDK
                response = await self._simulate_a2a_call(client, payload)
                return response

            except Exception as e:
                last_error = e
                self.logger.warning(f"Send attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)

        raise last_error or Exception("All retry attempts failed")

    async def _simulate_a2a_call(
        self, client: A2AClient, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate A2A client call. This will be replaced with actual A2A SDK calls.
        """
        # For now, return a mock response
        # In real implementation, this would be: await client.send(payload)
        return {
            "status": "success",
            "message_id": payload.get("message_id"),
            "timestamp": datetime.utcnow().isoformat(),
            "response": "Message received and processed",
        }

    def _message_to_a2a_payload(self, message: A2AMessage) -> Dict[str, Any]:
        """Convert our message format to A2A protocol format."""
        return {
            "id": message.message_id,
            "from": message.from_agent,
            "to": message.to_agent,
            "type": message.message_type.value,
            "content": message.content,
            "context": message.context,
            "timestamp": message.timestamp.isoformat(),
            "priority": message.priority.value,
            "correlation_id": message.correlation_id,
        }

    def _record_message(
        self, message: A2AMessage, response: Dict[str, Any], status: str
    ) -> None:
        """Record message in history for debugging and monitoring."""
        record = {
            "message_id": message.message_id,
            "from_agent": message.from_agent,
            "to_agent": message.to_agent,
            "message_type": message.message_type.value,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "response": response,
        }

        self.message_history.append(record)

        # Trim history to max size
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size :]

    async def _cleanup_stale_clients(self) -> None:
        """Clean up stale client connections."""
        current_time = datetime.utcnow()
        stale_clients = []

        for agent_id, last_used in self.client_last_used.items():
            if (current_time - last_used).seconds > self.client_cache_ttl:
                stale_clients.append(agent_id)

        for agent_id in stale_clients:
            if agent_id in self.clients:
                del self.clients[agent_id]
            del self.client_last_used[agent_id]
            self.logger.debug(f"Cleaned up stale client for agent: {agent_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get client manager statistics."""
        return {
            "agent_id": self.agent_id,
            "active_clients": len(self.clients),
            "message_history_size": len(self.message_history),
            "last_health_check": self.last_health_check.isoformat()
            if self.last_health_check
            else None,
            "discovery_configured": self.discovery is not None,
            "timestamp": datetime.utcnow().isoformat(),
        }
