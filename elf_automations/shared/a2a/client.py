"""
A2A Client for inter-team communication

This client enables teams to communicate with each other using
Google's A2A protocol through structured messages.

Updated to support both direct team-to-team communication and
routing through the A2A Gateway for better discovery and management.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class A2AClient:
    """Client for A2A (Agent-to-Agent) communication between teams"""

    def __init__(
        self,
        team_id: str,
        team_endpoint: str = "http://localhost:8090",
        timeout: int = 300,
        gateway_url: Optional[str] = None,
        use_gateway: bool = True,
    ):
        """
        Initialize A2A client

        Args:
            team_id: ID of the team using this client
            team_endpoint: Base URL of this team's A2A server
            timeout: Request timeout in seconds
            gateway_url: URL of the A2A Gateway (optional)
            use_gateway: Whether to route through gateway (default: True)
        """
        self.team_id = team_id
        self.team_endpoint = team_endpoint
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Gateway configuration
        self.use_gateway = use_gateway
        self.gateway_url = gateway_url or os.getenv("A2A_GATEWAY_URL", "http://a2a-gateway-service:8080")
        
        # Remove trailing slash
        if self.gateway_url:
            self.gateway_url = self.gateway_url.rstrip("/")

    async def send_task(
        self,
        target_team: str,
        task_description: str,
        context: Dict[str, Any] = None,
        deadline_seconds: int = 3600,
        required_capabilities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a task to another team

        Args:
            target_team: Name of the team to send task to (optional if using capabilities)
            task_description: What needs to be done
            context: Additional context for the task
            deadline_seconds: Time limit for task completion
            required_capabilities: Required capabilities (for gateway routing)

        Returns:
            Response from the target team
        """
        # Route through gateway if enabled
        if self.use_gateway and self.gateway_url:
            return await self._send_task_via_gateway(
                target_team=target_team,
                task_description=task_description,
                context=context,
                timeout=deadline_seconds,
                required_capabilities=required_capabilities
            )
        
        # Direct connection (legacy mode)
        target_url = f"http://{target_team}:8090/task"

        payload = {
            "from_team": self.team_id,
            "description": task_description,
            "context": context or {},
            "deadline_seconds": deadline_seconds,
        }

        logger.info(f"A2A Direct: {self.team_id} -> {target_team}: {task_description[:50]}...")

        try:
            response = await self.client.post(target_url, json=payload)
            response.raise_for_status()
            result = response.json()

            logger.info(
                f"A2A Direct: {target_team} completed task with status: {result.get('status')}"
            )
            return result

        except httpx.HTTPError as e:
            logger.error(f"A2A direct communication failed: {e}")
            return {"status": "error", "error": str(e), "team": target_team}

    async def _send_task_via_gateway(
        self,
        target_team: Optional[str],
        task_description: str,
        context: Optional[Dict[str, Any]],
        timeout: int,
        required_capabilities: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Send task through the A2A Gateway"""
        logger.info(f"A2A Gateway: {self.team_id} routing task: {task_description[:50]}...")
        
        payload = {
            "from_team": self.team_id,
            "task_description": task_description,
            "context": context or {},
            "timeout": timeout
        }
        
        if target_team:
            payload["to_team"] = target_team
            
        if required_capabilities:
            payload["required_capabilities"] = required_capabilities
        
        try:
            response = await self.client.post(
                f"{self.gateway_url}/route",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(
                f"A2A Gateway: Task routed to {result.get('routed_to', 'unknown')} "
                f"with status: {result.get('status', 'unknown')}"
            )
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"A2A Gateway routing failed: {e}")
            
            # Fallback to direct connection if gateway fails and target specified
            if target_team and not self.use_gateway:
                logger.warning("Falling back to direct connection")
                self.use_gateway = False
                result = await self.send_task(
                    target_team, task_description, context, timeout
                )
                self.use_gateway = True
                return result
            
            return {"status": "error", "error": str(e), "gateway_error": True}

    async def discover_teams(self, capability: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discover available teams through the gateway
        
        Args:
            capability: Filter by specific capability
            
        Returns:
            List of available teams
        """
        if not self.gateway_url:
            logger.warning("No gateway URL configured for team discovery")
            return []
        
        try:
            params = {}
            if capability:
                params["capability"] = capability
                
            response = await self.client.get(
                f"{self.gateway_url}/teams",
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to discover teams: {e}")
            return []

    async def get_capabilities(self, target_team: Optional[str] = None) -> Dict[str, Any]:
        """
        Get capabilities of a team or all available capabilities
        
        Args:
            target_team: Specific team to query (optional)
            
        Returns:
            Capabilities information
        """
        # If gateway is available and no specific team requested
        if self.gateway_url and not target_team:
            try:
                response = await self.client.get(f"{self.gateway_url}/capabilities")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to get capabilities from gateway: {e}")
                return {"error": str(e)}
        
        # Direct query to specific team
        if target_team:
            target_url = f"http://{target_team}:8090/capabilities"
            
            try:
                response = await self.client.get(target_url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to get capabilities from {target_team}: {e}")
                return {"error": str(e)}

    async def close(self):
        """Close the client connection"""
        await self.client.aclose()

    # Context manager support
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
