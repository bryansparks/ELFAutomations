"""
MCP Servers Package for ELF Automations

This package contains Model Context Protocol (MCP) servers that provide
standardized tool integration for the Virtual AI Company Platform.
"""

from .base import BaseMCPServer
from .business_tools import BusinessToolsServer

__all__ = [
    "BaseMCPServer",
    "BusinessToolsServer",
]

__version__ = "0.1.0"
