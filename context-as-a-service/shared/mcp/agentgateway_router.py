"""
AgentGateway MCP Router

Handles routing of MCP requests through AgentGateway with:
- Dynamic server discovery
- Protocol translation (stdio/http/sse)
- Credential injection
- Load balancing
- Health checking
"""

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .discovery import MCPServerInfo

logger = logging.getLogger(__name__)


@dataclass
class MCPServerInstance:
    """Running instance of an MCP server"""

    server_info: MCPServerInfo
    process: Optional[subprocess.Popen] = None
    endpoint: Optional[str] = None
    started_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"  # unknown, healthy, unhealthy
    request_count: int = 0
    error_count: int = 0

    @property
    def is_healthy(self) -> bool:
        return self.health_status == "healthy"

    @property
    def needs_health_check(self) -> bool:
        if not self.last_health_check:
            return True
        return datetime.now() - self.last_health_check > timedelta(seconds=30)


class MCPRouter:
    """Routes MCP requests to appropriate servers"""

    def __init__(
        self,
        gateway_config: Optional[Dict] = None,
        credential_resolver: Optional[Any] = None,
    ):
        """
        Initialize MCP Router

        Args:
            gateway_config: AgentGateway configuration
            credential_resolver: Function to resolve credential placeholders
        """
        self.config = gateway_config or {}
        self.credential_resolver = credential_resolver
        self._instances: Dict[str, MCPServerInstance] = {}
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def initialize(self):
        """Initialize router and start configured servers"""
        mcp_targets = self.config.get("targets", {}).get("mcp", [])

        for target in mcp_targets:
            try:
                await self._start_server(target)
            except Exception as e:
                logger.error(f"Failed to start MCP server {target.get('name')}: {e}")

    async def _start_server(self, target_config: Dict):
        """Start an MCP server based on configuration"""
        name = target_config.get("name")
        if not name:
            return

        # Create server info from config
        if "stdio" in target_config:
            stdio_config = target_config["stdio"]
            server_info = MCPServerInfo(
                name=name,
                protocol="stdio",
                command=stdio_config.get("cmd"),
                args=stdio_config.get("args", []),
                env=stdio_config.get("env", {}),
            )

            # Start stdio server
            instance = await self._start_stdio_server(server_info)

        elif "http" in target_config:
            http_config = target_config["http"]
            server_info = MCPServerInfo(
                name=name, protocol="http", endpoint=http_config.get("url")
            )
            instance = MCPServerInstance(
                server_info=server_info,
                endpoint=server_info.endpoint,
                started_at=datetime.now(),
            )

        elif "sse" in target_config:
            sse_config = target_config["sse"]
            server_info = MCPServerInfo(
                name=name, protocol="sse", endpoint=sse_config.get("url")
            )
            instance = MCPServerInstance(
                server_info=server_info,
                endpoint=server_info.endpoint,
                started_at=datetime.now(),
            )
        else:
            logger.warning(f"Unknown server type for {name}")
            return

        self._instances[name] = instance
        logger.info(f"Started MCP server: {name} ({server_info.protocol})")

    async def _start_stdio_server(
        self, server_info: MCPServerInfo
    ) -> MCPServerInstance:
        """Start a stdio-based MCP server"""
        instance = MCPServerInstance(server_info=server_info)

        # Resolve environment variables
        env = {}
        for key, value in server_info.env.items():
            if (
                self.credential_resolver
                and value.startswith("${")
                and value.endswith("}")
            ):
                resolved = self.credential_resolver(value[2:-1])
                if resolved:
                    env[key] = resolved
                else:
                    env[key] = value
            else:
                env[key] = value

        # Build command
        cmd = [server_info.command] + server_info.args

        # Start process
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, **env},
                text=True,
            )

            instance.process = process
            instance.started_at = datetime.now()
            instance.health_status = "healthy"  # Assume healthy on start

            # Give it a moment to start
            await asyncio.sleep(0.5)

            # Check if it's still running
            if process.poll() is not None:
                stderr = process.stderr.read() if process.stderr else ""
                raise Exception(f"Process exited immediately: {stderr}")

        except Exception as e:
            logger.error(f"Failed to start stdio server {server_info.name}: {e}")
            instance.health_status = "unhealthy"
            raise

        return instance

    async def route_request(
        self, server_name: str, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route an MCP request to the appropriate server"""
        instance = self._instances.get(server_name)
        if not instance:
            return {
                "error": f"Server '{server_name}' not found",
                "available_servers": list(self._instances.keys()),
            }

        # Update request count
        instance.request_count += 1

        # Check health if needed
        if instance.needs_health_check:
            await self._check_health(instance)

        if not instance.is_healthy:
            return {
                "error": f"Server '{server_name}' is unhealthy",
                "health_status": instance.health_status,
            }

        try:
            # Route based on protocol
            if instance.server_info.protocol == "stdio":
                result = await self._route_stdio(instance, method, params)
            elif instance.server_info.protocol == "http":
                result = await self._route_http(instance, method, params)
            elif instance.server_info.protocol == "sse":
                result = await self._route_sse(instance, method, params)
            else:
                result = {
                    "error": f"Unsupported protocol: {instance.server_info.protocol}"
                }

            return result

        except Exception as e:
            instance.error_count += 1
            logger.error(f"Error routing to {server_name}: {e}")
            return {"error": str(e), "server": server_name}

    async def _route_stdio(
        self, instance: MCPServerInstance, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route request to stdio-based MCP server"""
        if not instance.process:
            raise Exception("No process for stdio server")

        # Build JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": f"{instance.server_info.name}-{instance.request_count}",
        }

        # Send request
        request_json = json.dumps(request) + "\n"
        instance.process.stdin.write(request_json)
        instance.process.stdin.flush()

        # Read response
        response_line = instance.process.stdout.readline()
        if not response_line:
            raise Exception("No response from stdio server")

        response = json.loads(response_line.strip())

        # Extract result or error
        if "error" in response:
            return response["error"]
        else:
            return response.get("result", {})

    async def _route_http(
        self, instance: MCPServerInstance, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route request to HTTP-based MCP server"""
        if not instance.endpoint:
            raise Exception("No endpoint for HTTP server")

        # Build request URL
        url = f"{instance.endpoint}/{method}"

        # Send HTTP request
        response = await self._http_client.post(url, json=params)
        response.raise_for_status()

        return response.json()

    async def _route_sse(
        self, instance: MCPServerInstance, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route request to SSE-based MCP server"""
        # SSE is typically for streaming responses
        # For now, treat it like HTTP
        return await self._route_http(instance, method, params)

    async def _check_health(self, instance: MCPServerInstance):
        """Check health of an MCP server"""
        instance.last_health_check = datetime.now()

        try:
            if instance.server_info.protocol == "stdio":
                # Check if process is still running
                if instance.process and instance.process.poll() is None:
                    instance.health_status = "healthy"
                else:
                    instance.health_status = "unhealthy"

            elif instance.server_info.protocol in ["http", "sse"]:
                # Try health endpoint
                if instance.endpoint:
                    response = await self._http_client.get(
                        f"{instance.endpoint}/health", timeout=5.0
                    )
                    if response.status_code == 200:
                        instance.health_status = "healthy"
                    else:
                        instance.health_status = "unhealthy"

        except Exception as e:
            logger.warning(f"Health check failed for {instance.server_info.name}: {e}")
            instance.health_status = "unhealthy"

    async def list_servers(self) -> List[Dict[str, Any]]:
        """List all available MCP servers"""
        servers = []

        for name, instance in self._instances.items():
            servers.append(
                {
                    "name": name,
                    "protocol": instance.server_info.protocol,
                    "status": instance.health_status,
                    "requests": instance.request_count,
                    "errors": instance.error_count,
                    "uptime": str(datetime.now() - instance.started_at)
                    if instance.started_at
                    else "N/A",
                }
            )

        return servers

    async def get_server_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Get available tools from a server"""
        result = await self.route_request(server_name, "tools/list", {})

        if "error" in result:
            return []

        return result.get("tools", [])

    async def shutdown(self):
        """Shutdown all MCP servers"""
        for name, instance in self._instances.items():
            if instance.process:
                logger.info(f"Stopping MCP server: {name}")
                instance.process.terminate()
                try:
                    instance.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    instance.process.kill()

        await self._http_client.aclose()


def create_agentgateway_routes(router: MCPRouter):
    """Create FastAPI routes for AgentGateway MCP integration"""
    from fastapi import APIRouter, HTTPException

    api = APIRouter(prefix="/mcp", tags=["mcp"])

    @api.get("/servers")
    async def list_servers():
        """List all available MCP servers"""
        return await router.list_servers()

    @api.get("/{server}/tools")
    async def list_tools(server: str):
        """List tools available on a server"""
        tools = await router.get_server_tools(server)
        if not tools:
            raise HTTPException(status_code=404, detail=f"Server '{server}' not found")
        return tools

    @api.post("/{server}/tools/{tool}")
    async def call_tool(server: str, tool: str, request: Dict[str, Any]):
        """Call a tool on an MCP server"""
        result = await router.route_request(
            server, f"tools/{tool}", request.get("arguments", {})
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    return api
