"""
Mock A2A Client for testing without actual network calls
"""

import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MockA2AClient:
    """Mock A2A client for testing"""

    def __init__(self, team_id: str, **kwargs):
        self.team_id = team_id
        self.sent_tasks = []

    async def send_task(
        self,
        target_team: str,
        task_description: str,
        context: Dict[str, Any] = None,
        deadline_seconds: int = 3600,
    ) -> Dict[str, Any]:
        """Mock task sending - just logs and returns success"""

        task = {
            "from_team": self.team_id,
            "to_team": target_team,
            "description": task_description,
            "context": context or {},
        }

        self.sent_tasks.append(task)
        logger.info(
            f"MOCK A2A: {self.team_id} -> {target_team}: {task_description[:50]}..."
        )

        # Simulate some processing time
        await asyncio.sleep(0.1)

        # Return mock successful response
        return {
            "status": "success",
            "team": target_team,
            "result": f"Mock result for: {task_description[:30]}...",
            "mock": True,
        }

    async def get_capabilities(self, target_team: str) -> Dict[str, Any]:
        """Mock capabilities response"""
        return {
            "team": target_team,
            "capabilities": ["mock_capability_1", "mock_capability_2"],
            "mock": True,
        }

    async def close(self):
        """Mock close"""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
