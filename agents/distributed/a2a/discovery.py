"""
A2A discovery service for agent registration and discovery.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

# Real A2A SDK imports - REQUIRED, no fallback
from a2a.types import AgentCard


class DiscoveryService:
    """
    Service for registering and discovering A2A agents.
    Provides a centralized registry for agent capabilities and endpoints.
    """

    def __init__(self, discovery_endpoint: Optional[str] = None):
        """Initialize the discovery service."""
        self.discovery_endpoint = discovery_endpoint
        self.timeout = 30.0

        # Local agent registry (fallback when no central discovery)
        self.local_registry: Dict[str, AgentCard] = {}
        self.registration_timestamps: Dict[str, datetime] = {}
        self.agent_ttl = 300  # 5 minutes

        self.logger = logging.getLogger("a2a_discovery")

        if discovery_endpoint:
            self.logger.info(
                f"Discovery service configured with endpoint: {discovery_endpoint}"
            )
        else:
            self.logger.info("Using local discovery registry (no central endpoint)")

    async def register_agent(self, agent_card: AgentCard) -> bool:
        """Register an agent with the discovery service."""
        try:
            if self.discovery_endpoint:
                # Register with central discovery service
                return await self._register_with_central_service(agent_card)
            else:
                # Register in local registry
                return await self._register_locally(agent_card)

        except Exception as e:
            self.logger.error(f"Failed to register agent {agent_card.agent_id}: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the discovery service."""
        try:
            if self.discovery_endpoint:
                # Unregister from central discovery service
                return await self._unregister_from_central_service(agent_id)
            else:
                # Unregister from local registry
                return await self._unregister_locally(agent_id)

        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Get information about a specific agent."""
        try:
            if self.discovery_endpoint:
                # Query central discovery service
                return await self._get_agent_from_central_service(agent_id)
            else:
                # Query local registry
                return await self._get_agent_locally(agent_id)

        except Exception as e:
            self.logger.error(f"Failed to get agent {agent_id}: {e}")
            return None

    async def discover_agents(
        self, capabilities: Optional[List[str]] = None
    ) -> List[AgentCard]:
        """Discover agents, optionally filtered by capabilities."""
        try:
            if self.discovery_endpoint:
                # Query central discovery service
                return await self._discover_from_central_service(capabilities)
            else:
                # Query local registry
                return await self._discover_locally(capabilities)

        except Exception as e:
            self.logger.error(f"Failed to discover agents: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if the discovery service is healthy."""
        try:
            if self.discovery_endpoint:
                # Check central discovery service
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.discovery_endpoint}/health")
                    return response.status_code == 200
            else:
                # Local registry is always "healthy"
                await self._cleanup_expired_agents()
                return True

        except Exception as e:
            self.logger.error(f"Discovery service health check failed: {e}")
            return False

    async def _register_with_central_service(self, agent_card: AgentCard) -> bool:
        """Register agent with central discovery service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "name": agent_card.name,
                    "description": agent_card.description,
                    "version": agent_card.version,
                    "url": agent_card.url,
                    "capabilities": agent_card.capabilities.model_dump(),
                    "defaultInputModes": agent_card.defaultInputModes,
                    "defaultOutputModes": agent_card.defaultOutputModes,
                    "skills": agent_card.skills,
                    "registered_at": datetime.utcnow().isoformat(),
                }

                response = await client.post(
                    f"{self.discovery_endpoint}/agents", json=payload
                )

                if response.status_code in [200, 201]:
                    self.logger.info(
                        f"Agent {agent_card.agent_id} registered with central discovery"
                    )
                    return True
                else:
                    self.logger.error(
                        f"Central discovery registration failed: {response.status_code}"
                    )
                    return False

        except Exception as e:
            self.logger.error(f"Failed to register with central discovery: {e}")
            return False

    async def _register_locally(self, agent_card: AgentCard) -> bool:
        """Register agent in local registry."""
        self.local_registry[agent_card.agent_id] = agent_card
        self.registration_timestamps[agent_card.agent_id] = datetime.utcnow()

        self.logger.info(f"Agent {agent_card.agent_id} registered locally")
        return True

    async def _unregister_from_central_service(self, agent_id: str) -> bool:
        """Unregister agent from central discovery service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.discovery_endpoint}/agents/{agent_id}"
                )

                if response.status_code in [200, 204, 404]:
                    self.logger.info(
                        f"Agent {agent_id} unregistered from central discovery"
                    )
                    return True
                else:
                    self.logger.error(
                        f"Central discovery unregistration failed: {response.status_code}"
                    )
                    return False

        except Exception as e:
            self.logger.error(f"Failed to unregister from central discovery: {e}")
            return False

    async def _unregister_locally(self, agent_id: str) -> bool:
        """Unregister agent from local registry."""
        if agent_id in self.local_registry:
            del self.local_registry[agent_id]

        if agent_id in self.registration_timestamps:
            del self.registration_timestamps[agent_id]

        self.logger.info(f"Agent {agent_id} unregistered locally")
        return True

    async def _get_agent_from_central_service(
        self, agent_id: str
    ) -> Optional[AgentCard]:
        """Get agent information from central discovery service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.discovery_endpoint}/agents/{agent_id}"
                )

                if response.status_code == 200:
                    data = response.json()
                    return AgentCard(
                        agent_id=data["agent_id"],
                        name=data["name"],
                        description=data["description"],
                        capabilities=data["capabilities"],
                        endpoints=data["endpoints"],
                        metadata=data.get("metadata", {}),
                    )
                elif response.status_code == 404:
                    return None
                else:
                    self.logger.error(
                        f"Failed to get agent from central discovery: {response.status_code}"
                    )
                    return None

        except Exception as e:
            self.logger.error(f"Failed to get agent from central discovery: {e}")
            return None

    async def _get_agent_locally(self, agent_id: str) -> Optional[AgentCard]:
        """Get agent information from local registry."""
        await self._cleanup_expired_agents()
        return self.local_registry.get(agent_id)

    async def _discover_from_central_service(
        self, capabilities: Optional[List[str]] = None
    ) -> List[AgentCard]:
        """Discover agents from central discovery service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                if capabilities:
                    params["capabilities"] = ",".join(capabilities)

                response = await client.get(
                    f"{self.discovery_endpoint}/agents", params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    agents = []

                    for agent_data in data.get("agents", []):
                        agent_card = AgentCard(
                            agent_id=agent_data["agent_id"],
                            name=agent_data["name"],
                            description=agent_data["description"],
                            capabilities=agent_data["capabilities"],
                            endpoints=agent_data["endpoints"],
                            metadata=agent_data.get("metadata", {}),
                        )
                        agents.append(agent_card)

                    return agents
                else:
                    self.logger.error(
                        f"Failed to discover agents from central service: {response.status_code}"
                    )
                    return []

        except Exception as e:
            self.logger.error(f"Failed to discover agents from central service: {e}")
            return []

    async def _discover_locally(
        self, capabilities: Optional[List[str]] = None
    ) -> List[AgentCard]:
        """Discover agents from local registry."""
        await self._cleanup_expired_agents()

        agents = list(self.local_registry.values())

        # Filter by capabilities if specified
        if capabilities:
            filtered_agents = []
            for agent in agents:
                if any(cap in agent.capabilities for cap in capabilities):
                    filtered_agents.append(agent)
            agents = filtered_agents

        return agents

    async def _cleanup_expired_agents(self) -> None:
        """Clean up expired agent registrations from local registry."""
        current_time = datetime.utcnow()
        expired_agents = []

        for agent_id, registration_time in self.registration_timestamps.items():
            if (current_time - registration_time).seconds > self.agent_ttl:
                expired_agents.append(agent_id)

        for agent_id in expired_agents:
            if agent_id in self.local_registry:
                del self.local_registry[agent_id]
            del self.registration_timestamps[agent_id]
            self.logger.debug(f"Cleaned up expired agent registration: {agent_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get discovery service statistics."""
        return {
            "discovery_endpoint": self.discovery_endpoint,
            "local_registry_size": len(self.local_registry),
            "registered_agents": list(self.local_registry.keys()),
            "agent_ttl_seconds": self.agent_ttl,
            "timestamp": datetime.utcnow().isoformat(),
        }
