"""
A2A (Agent-to-Agent) Communication Module

Provides client and server implementations for inter-team communication.
"""

from .chat_messages import (
    ChatCoordinator,
    ChatDelegationConfirmed,
    ChatDelegationReady,
    ChatHandoff,
    ChatInitiationRequest,
    ChatInitiationResponse,
    ChatMessage,
    ChatMessageType,
    ChatSessionEnd,
    ChatStatus,
    ChatStatusUpdate,
)
from .client import A2AClient
from .messages import A2AMessage, MessagePriority
from .mock_client import MockA2AClient
from .project_messages import (
    ProgressUpdateMessage,
    ProjectAssignmentMessage,
    ProjectCoordinator,
    TaskAssignmentMessage,
)

__all__ = [
    "A2AClient",
    "MockA2AClient",
    "A2AMessage",
    "MessagePriority",
    # Chat messages
    "ChatInitiationRequest",
    "ChatInitiationResponse",
    "ChatMessage",
    "ChatStatusUpdate",
    "ChatDelegationReady",
    "ChatDelegationConfirmed",
    "ChatSessionEnd",
    "ChatHandoff",
    "ChatCoordinator",
    "ChatMessageType",
    "ChatStatus",
    # Project messages
    "ProjectAssignmentMessage",
    "TaskAssignmentMessage",
    "ProgressUpdateMessage",
    "ProjectCoordinator",
]
