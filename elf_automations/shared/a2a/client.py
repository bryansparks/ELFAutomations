"""
A2A Client for inter-team communication

This client enables teams to communicate with each other using
Google's A2A protocol through structured messages.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class A2AClient:
    """Client for A2A (Agent-to-Agent) communication between teams"""

    def __init__(
        self,
        team_id: str,
        team_endpoint: str = "http://localhost:8090",
        timeout: int = 300,
    ):
        """
        Initialize A2A client

        Args:
            team_id: ID of the team using this client
            team_endpoint: Base URL of this team's A2A server
            timeout: Request timeout in seconds
        """
        self.team_id = team_id
        self.team_endpoint = team_endpoint
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def send_task(
        self,
        target_team: str,
        task_description: str,
        context: Dict[str, Any] = None,
        deadline_seconds: int = 3600,
    ) -> Dict[str, Any]:
        """
        Send a task to another team

        Args:
            target_team: Name of the team to send task to
            task_description: What needs to be done
            context: Additional context for the task
            deadline_seconds: Time limit for task completion

        Returns:
            Response from the target team
        """
        # In real implementation, this would route through AgentGateway
        # For now, direct connection to team endpoints
        target_url = f"http://{target_team}:8090/task"

        payload = {
            "from_team": self.team_id,
            "description": task_description,
            "context": context or {},
            "deadline_seconds": deadline_seconds,
        }

        logger.info(f"A2A: {self.team_id} -> {target_team}: {task_description[:50]}...")

        try:
            response = await self.client.post(target_url, json=payload)
            response.raise_for_status()
            result = response.json()

            logger.info(
                f"A2A: {target_team} completed task with status: {result.get('status')}"
            )
            return result

        except httpx.HTTPError as e:
            logger.error(f"A2A communication failed: {e}")
            return {"status": "error", "error": str(e), "team": target_team}

    async def get_capabilities(self, target_team: str) -> Dict[str, Any]:
        """Get the capabilities of another team"""
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
