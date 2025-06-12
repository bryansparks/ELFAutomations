"""
A2A (Agent-to-Agent) communication infrastructure for distributed agents.
"""

from .client import A2AClientManager
from .discovery import DiscoveryService
from .messages import A2AMessage, MessageType

__all__ = ["A2AClientManager", "A2AMessage", "MessageType", "DiscoveryService"]
