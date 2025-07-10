"""
Chat-related A2A message types for team chat interface.

These messages enable chat sessions between users and team managers,
and the subsequent delegation of tasks based on chat outcomes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .messages import A2AMessage


class ChatMessageType(Enum):
    """Types of chat-related messages."""

    CHAT_INITIATION_REQUEST = "chat_initiation_request"
    CHAT_INITIATION_RESPONSE = "chat_initiation_response"
    CHAT_MESSAGE = "chat_message"
    CHAT_STATUS_UPDATE = "chat_status_update"
    CHAT_DELEGATION_READY = "chat_delegation_ready"
    CHAT_DELEGATION_CONFIRMED = "chat_delegation_confirmed"
    CHAT_SESSION_END = "chat_session_end"
    CHAT_HANDOFF = "chat_handoff"


class ChatStatus(Enum):
    """Status of a chat session."""

    INITIATING = "initiating"
    ACTIVE = "active"
    THINKING = "thinking"
    WAITING_FOR_USER = "waiting_for_user"
    PREPARING_DELEGATION = "preparing_delegation"
    DELEGATION_READY = "delegation_ready"
    ENDED = "ended"
    ERROR = "error"


@dataclass
class ChatInitiationRequest(A2AMessage):
    """Request to start an interactive chat session with a team manager."""

    user_id: str
    session_id: str
    initial_context: Dict[str, Any] = field(default_factory=dict)
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    chat_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.type = ChatMessageType.CHAT_INITIATION_REQUEST.value


@dataclass
class ChatInitiationResponse(A2AMessage):
    """Response to chat initiation request."""

    session_id: str
    accepted: bool
    manager_name: str
    manager_role: str
    rejection_reason: Optional[str] = None
    initial_greeting: Optional[str] = None
    available_actions: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.type = ChatMessageType.CHAT_INITIATION_RESPONSE.value


@dataclass
class ChatMessage(A2AMessage):
    """A message within a chat session."""

    session_id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.type = ChatMessageType.CHAT_MESSAGE.value


@dataclass
class ChatStatusUpdate(A2AMessage):
    """Update on chat session status."""

    session_id: str
    status: str  # One of ChatStatus enum values
    message_count: int
    total_tokens: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.type = ChatMessageType.CHAT_STATUS_UPDATE.value


@dataclass
class ChatDelegationReady(A2AMessage):
    """Manager is ready to delegate after chat."""

    session_id: str
    task_specification: Dict[str, Any]
    chat_summary: str
    confidence_level: float  # 0.0 to 1.0
    suggested_teams: List[str]
    estimated_effort: Optional[str] = None
    requires_user_confirmation: bool = True

    def __post_init__(self):
        self.type = ChatMessageType.CHAT_DELEGATION_READY.value


@dataclass
class ChatDelegationConfirmed(A2AMessage):
    """User confirmed delegation after chat."""

    session_id: str
    delegation_id: str
    confirmed: bool
    user_modifications: Optional[Dict[str, Any]] = None
    target_teams: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.type = ChatMessageType.CHAT_DELEGATION_CONFIRMED.value


@dataclass
class ChatSessionEnd(A2AMessage):
    """Chat session has ended."""

    session_id: str
    end_reason: str  # 'user_ended', 'timeout', 'delegation_complete', 'error'
    total_messages: int
    total_tokens: int
    duration_seconds: float
    delegation_created: bool = False
    delegation_id: Optional[str] = None

    def __post_init__(self):
        self.type = ChatMessageType.CHAT_SESSION_END.value


@dataclass
class ChatHandoff(A2AMessage):
    """Handoff chat session to another team."""

    session_id: str
    from_team: str
    to_team: str
    handoff_reason: str
    chat_history_summary: str
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.type = ChatMessageType.CHAT_HANDOFF.value


class ChatCoordinator:
    """Helper class for chat-related A2A communications."""

    @staticmethod
    def create_chat_initiation(
        user_id: str,
        session_id: str,
        sender: str,
        recipient: str,
        initial_context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ChatInitiationRequest:
        """Create a chat initiation request."""
        return ChatInitiationRequest(
            sender=sender,
            recipient=recipient,
            user_id=user_id,
            session_id=session_id,
            initial_context=initial_context or {},
            **kwargs,
        )

    @staticmethod
    def create_chat_response(
        session_id: str,
        accepted: bool,
        manager_name: str,
        manager_role: str,
        sender: str,
        recipient: str,
        **kwargs,
    ) -> ChatInitiationResponse:
        """Create a chat initiation response."""
        return ChatInitiationResponse(
            sender=sender,
            recipient=recipient,
            session_id=session_id,
            accepted=accepted,
            manager_name=manager_name,
            manager_role=manager_role,
            **kwargs,
        )

    @staticmethod
    def create_chat_message(
        session_id: str,
        role: str,
        content: str,
        sender: str,
        recipient: str,
        **kwargs,
    ) -> ChatMessage:
        """Create a chat message."""
        return ChatMessage(
            sender=sender,
            recipient=recipient,
            session_id=session_id,
            role=role,
            content=content,
            **kwargs,
        )

    @staticmethod
    def create_delegation_ready(
        session_id: str,
        task_specification: Dict[str, Any],
        chat_summary: str,
        sender: str,
        recipient: str,
        confidence_level: float = 0.8,
        **kwargs,
    ) -> ChatDelegationReady:
        """Create a delegation ready message."""
        return ChatDelegationReady(
            sender=sender,
            recipient=recipient,
            session_id=session_id,
            task_specification=task_specification,
            chat_summary=chat_summary,
            confidence_level=confidence_level,
            **kwargs,
        )

    @staticmethod
    def create_session_end(
        session_id: str,
        end_reason: str,
        total_messages: int,
        total_tokens: int,
        duration_seconds: float,
        sender: str,
        recipient: str,
        **kwargs,
    ) -> ChatSessionEnd:
        """Create a session end message."""
        return ChatSessionEnd(
            sender=sender,
            recipient=recipient,
            session_id=session_id,
            end_reason=end_reason,
            total_messages=total_messages,
            total_tokens=total_tokens,
            duration_seconds=duration_seconds,
            **kwargs,
        )

    @staticmethod
    def parse_chat_message(message_data: Dict[str, Any]) -> A2AMessage:
        """Parse a chat message from raw data."""
        msg_type = message_data.get("type")

        message_classes = {
            ChatMessageType.CHAT_INITIATION_REQUEST.value: ChatInitiationRequest,
            ChatMessageType.CHAT_INITIATION_RESPONSE.value: ChatInitiationResponse,
            ChatMessageType.CHAT_MESSAGE.value: ChatMessage,
            ChatMessageType.CHAT_STATUS_UPDATE.value: ChatStatusUpdate,
            ChatMessageType.CHAT_DELEGATION_READY.value: ChatDelegationReady,
            ChatMessageType.CHAT_DELEGATION_CONFIRMED.value: ChatDelegationConfirmed,
            ChatMessageType.CHAT_SESSION_END.value: ChatSessionEnd,
            ChatMessageType.CHAT_HANDOFF.value: ChatHandoff,
        }

        message_class = message_classes.get(msg_type)
        if not message_class:
            raise ValueError(f"Unknown chat message type: {msg_type}")

        # Remove type field as it's set in __post_init__
        data = {k: v for k, v in message_data.items() if k != "type"}

        return message_class(**data)
