"""
Base A2A message types and structures for agent communication.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class MessagePriority(Enum):
    """Message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class A2AMessage:
    """
    Base class for all A2A messages.
    """

    # Message routing
    sender: str
    recipient: str

    # Message identification
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Message metadata
    type: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    priority: str = MessagePriority.NORMAL.value

    # Message content
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "correlation_id": self.correlation_id,
            "type": self.type,
            "sender": self.sender,
            "recipient": self.recipient,
            "timestamp": self.timestamp,
            "priority": self.priority,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """Create message from dictionary."""
        return cls(**data)
