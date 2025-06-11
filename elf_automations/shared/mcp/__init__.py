"""
MCP (Model Context Protocol) Client Module

Provides client for communicating with MCP servers through AgentGateway.
"""

from .agentgateway_router import (
    MCPRouter,
    MCPServerInstance,
    create_agentgateway_routes,
)
from .client import MCPClient, SyncMCPClient
from .discovery import MCPDiscovery, MCPServerInfo, discover_mcp_servers
from .mock_client import MockMCPClient

__all__ = [
    "MCPClient",
    "SyncMCPClient",
    "MockMCPClient",
    "MCPDiscovery",
    "MCPServerInfo",
    "discover_mcp_servers",
    "MCPRouter",
    "MCPServerInstance",
    "create_agentgateway_routes",
]
