"""
ELF Automations - Virtual AI Company Platform
Agents Package

This package contains all AI agent implementations for the Virtual AI Company Platform.
"""

from .base import BaseAgent, AgentConfig, AgentState, AgentType
from .registry import AgentRegistry

__all__ = [
    "BaseAgent",
    "AgentConfig", 
    "AgentState",
    "AgentType",
    "AgentRegistry",
]

__version__ = "0.1.0"
