"""
A2A (Agent-to-Agent) communication infrastructure for distributed agents.
"""

from .client import A2AClientManager
from .messages import A2AMessage, MessageType
from .discovery import DiscoveryService

__all__ = [
    "A2AClientManager",
    "A2AMessage", 
    "MessageType",
    "DiscoveryService"
]
