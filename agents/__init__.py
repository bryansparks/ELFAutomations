"""
ELF Automations - Virtual AI Company Platform
Agents Package

This package contains all AI agent implementations for the Virtual AI Company Platform.
"""

from .base import AgentConfig, AgentState, AgentType, BaseAgent
from .registry import AgentRegistry

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "AgentState",
    "AgentType",
    "AgentRegistry",
]

__version__ = "0.1.0"
