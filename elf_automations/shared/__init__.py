"""
Shared modules for all ElfAutomations teams

Provides common functionality:
- A2A communication
- MCP client for AgentGateway
- Quota management
- Utilities
"""

from . import a2a, mcp, quota, utils

__all__ = ["a2a", "mcp", "quota", "utils"]
