"""
Mock MCP Client for testing without AgentGateway
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MockMCPClient:
    """Mock MCP client for testing"""

    def __init__(
        self,
        gateway_url: str = "http://mock-gateway",
        team_id: Optional[str] = None,
        **kwargs,
    ):
        self.gateway_url = gateway_url
        self.team_id = team_id
        self.call_history = []

    async def call_tool(
        self, server: str, tool: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock tool call - just logs and returns mock data"""

        call = {
            "server": server,
            "tool": tool,
            "arguments": arguments,
            "team_id": self.team_id,
        }

        self.call_history.append(call)
        logger.info(f"MOCK MCP: {server}.{tool} from team {self.team_id}")

        # Simulate processing time
        await asyncio.sleep(0.1)

        # Return mock responses based on server/tool
        if server == "supabase":
            if tool == "query_database":
                return {
                    "status": "success",
                    "data": [{"id": 1, "name": "mock_team"}],
                    "mock": True,
                }
            elif tool == "insert_record":
                return {"status": "success", "id": "mock-uuid", "mock": True}

        elif server == "twilio":
            if tool == "send_sms":
                return {
                    "status": "success",
                    "message_sid": "mock-message-id",
                    "mock": True,
                }

        # Generic mock response
        return {
            "status": "success",
            "server": server,
            "tool": tool,
            "result": "mock result",
            "mock": True,
        }

    async def list_tools(self, server: str) -> List[Dict[str, Any]]:
        """Mock tool listing"""
        if server == "supabase":
            return [
                {"name": "query_database", "description": "Execute SQL query"},
                {"name": "insert_record", "description": "Insert record"},
            ]
        elif server == "twilio":
            return [
                {"name": "send_sms", "description": "Send SMS message"},
                {"name": "receive_sms", "description": "Handle incoming SMS"},
            ]
        return []

    async def list_servers(self) -> List[str]:
        """Mock server listing"""
        return ["supabase", "twilio", "market-research", "code-generator"]

    async def supabase(self, tool: str, **kwargs) -> Dict[str, Any]:
        """Mock Supabase shortcut"""
        return await self.call_tool("supabase", tool, kwargs)

    async def twilio(self, tool: str, **kwargs) -> Dict[str, Any]:
        """Mock Twilio shortcut"""
        return await self.call_tool("twilio", tool, kwargs)

    async def close(self):
        """Mock close"""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
