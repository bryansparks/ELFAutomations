"""
A2A (Agent-to-Agent) Communication Module

Provides client and server implementations for inter-team communication.
"""

from .client import A2AClient
from .mock_client import MockA2AClient

__all__ = ["A2AClient", "MockA2AClient"]
