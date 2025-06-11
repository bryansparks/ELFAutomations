"""
MCP Client for accessing MCP servers through AgentGateway

All MCP communication goes through AgentGateway for:
- Authentication and authorization
- Rate limiting
- Monitoring and logging
- Load balancing
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from ..credentials.credential_manager import CredentialManager, CredentialType
from .discovery import MCPDiscovery, MCPServerInfo

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for accessing MCP servers through AgentGateway"""

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        team_id: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 60,
        credential_manager: Optional[CredentialManager] = None,
        auto_discover: bool = True,
    ):
        """
        Initialize MCP client

        Args:
            gateway_url: AgentGateway URL (auto-discovered if not provided)
            team_id: ID of the team using this client (for tracking)
            api_key: API key for AgentGateway authentication
            timeout: Request timeout in seconds
            credential_manager: Credential manager for secure credential access
            auto_discover: Whether to auto-discover MCP servers
        """
        self.team_id = team_id
        self.timeout = timeout
        self.credential_manager = credential_manager

        # Auto-discover gateway URL if not provided
        if not gateway_url:
            gateway_url = self._discover_gateway_url()
        self.gateway_url = gateway_url.rstrip("/")

        # Get API key from credential manager if available and not provided
        if not api_key and self.credential_manager and self.team_id:
            try:
                api_key = self.credential_manager.get_credential(
                    "agentgateway_api_key", team=self.team_id
                )
            except Exception as e:
                logger.debug(f"Could not get API key from credential manager: {e}")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if team_id:
            headers["X-Team-ID"] = team_id

        self.client = httpx.AsyncClient(timeout=timeout, headers=headers)

        # Initialize discovery service
        self.discovery = MCPDiscovery(use_agentgateway=True)
        self._available_servers: Dict[str, MCPServerInfo] = {}

        if auto_discover:
            # Run discovery in background
            asyncio.create_task(self._async_discover())

    async def call_tool(
        self, server: str, tool: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool on an MCP server

        Args:
            server: Name of the MCP server (e.g., "supabase", "twilio")
            tool: Name of the tool to call
            arguments: Arguments for the tool

        Returns:
            Response from the MCP server
        """
        endpoint = f"{self.gateway_url}/mcp/{server}/tools/{tool}"

        payload = {"arguments": arguments}

        logger.info(f"MCP call: {server}.{tool} from team {self.team_id}")

        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()

            logger.debug(f"MCP response: {result.get('status', 'unknown')}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"MCP call failed: {e}")
            return {"error": str(e), "server": server, "tool": tool}

    async def list_tools(self, server: str) -> List[Dict[str, Any]]:
        """List available tools on an MCP server"""
        endpoint = f"{self.gateway_url}/mcp/{server}/tools"

        try:
            response = await self.client.get(endpoint)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to list tools for {server}: {e}")
            return []

    async def list_servers(self) -> List[str]:
        """List available MCP servers"""
        endpoint = f"{self.gateway_url}/mcp/servers"

        try:
            response = await self.client.get(endpoint)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to list MCP servers: {e}")
            return []

    # Specific server shortcuts
    async def supabase(self, tool: str, **kwargs) -> Dict[str, Any]:
        """Shortcut for Supabase MCP calls"""
        return await self.call_tool("supabase", tool, kwargs)

    async def twilio(self, tool: str, **kwargs) -> Dict[str, Any]:
        """Shortcut for Twilio MCP calls"""
        return await self.call_tool("twilio", tool, kwargs)

    async def close(self):
        """Close the client connection"""
        await self.client.aclose()

    # Context manager support
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _discover_gateway_url(self) -> str:
        """Auto-discover AgentGateway URL"""
        # Check environment variable first
        if "AGENTGATEWAY_URL" in os.environ:
            return os.environ["AGENTGATEWAY_URL"]

        # Try common URLs in order
        urls = [
            "http://agentgateway:3000",
            "http://agentgateway.elf-automations:3000",
            "http://agentgateway.dev:3000",
            "http://localhost:3000",
        ]

        for url in urls:
            try:
                response = httpx.get(f"{url}/health", timeout=2.0)
                if response.status_code == 200:
                    logger.info(f"Auto-discovered AgentGateway at {url}")
                    return url
            except Exception:
                continue

        # Default fallback
        logger.warning("Could not auto-discover AgentGateway, using default")
        return "http://agentgateway.dev"

    async def _async_discover(self):
        """Run server discovery asynchronously"""
        try:
            self._available_servers = await asyncio.to_thread(
                self.discovery.discover_all
            )
            logger.info(f"Discovered {len(self._available_servers)} MCP servers")
        except Exception as e:
            logger.warning(f"Failed to discover MCP servers: {e}")

    async def refresh_servers(self) -> Dict[str, MCPServerInfo]:
        """Manually refresh the list of available servers"""
        await self._async_discover()
        return self._available_servers

    def get_available_servers(self) -> List[str]:
        """Get list of discovered server names"""
        return list(self._available_servers.keys())

    async def call_tool_with_env(
        self,
        server: str,
        tool: str,
        arguments: Dict[str, Any],
        env_overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Call a tool with environment variable overrides
        Useful for servers that need specific credentials
        """
        endpoint = f"{self.gateway_url}/mcp/{server}/tools/{tool}"

        payload = {"arguments": arguments}

        # Add environment overrides if provided
        if env_overrides:
            payload["env"] = env_overrides

        # Try to get server-specific credentials from credential manager
        if self.credential_manager and self.team_id:
            server_info = self._available_servers.get(server)
            if server_info and server_info.env:
                env = {}
                for key, value in server_info.env.items():
                    # Check if value is a credential reference
                    if value.startswith("${") and value.endswith("}"):
                        cred_name = value[2:-1]
                        try:
                            actual_value = self.credential_manager.get_credential(
                                cred_name, team=self.team_id
                            )
                            env[key] = actual_value
                        except Exception:
                            # Use original value if credential lookup fails
                            env[key] = value
                    else:
                        env[key] = value

                if env:
                    payload.setdefault("env", {}).update(env)

        logger.info(f"MCP call: {server}.{tool} from team {self.team_id}")

        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()

            logger.debug(f"MCP response: {result.get('status', 'unknown')}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"MCP call failed: {e}")
            return {"error": str(e), "server": server, "tool": tool}


# Synchronous wrapper for teams that aren't async
class SyncMCPClient:
    """Synchronous wrapper for MCPClient"""

    def __init__(self, *args, **kwargs):
        self._client = MCPClient(*args, **kwargs)
        self._loop = asyncio.new_event_loop()

    def call_tool(
        self, server: str, tool: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synchronous version of call_tool"""
        return self._loop.run_until_complete(
            self._client.call_tool(server, tool, arguments)
        )

    def list_tools(self, server: str) -> List[Dict[str, Any]]:
        """Synchronous version of list_tools"""
        return self._loop.run_until_complete(self._client.list_tools(server))

    def list_servers(self) -> List[str]:
        """Synchronous version of list_servers"""
        return self._loop.run_until_complete(self._client.list_servers())

    def close(self):
        """Close the client"""
        self._loop.run_until_complete(self._client.close())
        self._loop.close()
