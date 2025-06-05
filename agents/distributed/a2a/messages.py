"""
A2A message types and structures for agent communication.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List, Union, Literal
from pydantic import BaseModel, Field


class MessageType(Enum):
    """Types of A2A messages."""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_RESPONSE = "collaboration_response"
    STATUS_UPDATE = "status_update"
    CAPABILITY_QUERY = "capability_query"
    CAPABILITY_RESPONSE = "capability_response"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    CUSTOM = "custom"


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class A2AMessage(BaseModel):
    """
    Standard A2A message structure for agent communication.
    """
    
    # Message identification
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = Field(default=None, description="ID for grouping related messages")
    correlation_id: Optional[str] = Field(default=None, description="ID for request/response correlation")
    
    # Message routing
    from_agent: str = Field(..., description="Source agent ID")
    to_agent: str = Field(..., description="Target agent ID")
    
    # Message metadata
    message_type: MessageType = Field(..., description="Type of message")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None, description="Message expiration time")
    
    # Message content
    content: Dict[str, Any] = Field(default_factory=dict, description="Message payload")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    
    # Delivery tracking
    retry_count: int = Field(default=0, description="Number of delivery attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            MessageType: lambda v: v.value,
            MessagePriority: lambda v: v.value
        }


class TaskRequestMessage(A2AMessage):
    """Specialized message for task requests."""
    
    message_type: Literal[MessageType.TASK_REQUEST] = Field(default=MessageType.TASK_REQUEST)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Ensure content has required task fields
        if 'task_description' not in self.content:
            raise ValueError("TaskRequestMessage requires 'task_description' in content")


class TaskResponseMessage(A2AMessage):
    """Specialized message for task responses."""
    
    message_type: Literal[MessageType.TASK_RESPONSE] = Field(default=MessageType.TASK_RESPONSE)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Ensure content has required response fields
        if 'status' not in self.content:
            raise ValueError("TaskResponseMessage requires 'status' in content")


class CollaborationRequestMessage(A2AMessage):
    """Specialized message for collaboration requests."""
    
    message_type: Literal[MessageType.COLLABORATION_REQUEST] = Field(default=MessageType.COLLABORATION_REQUEST)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Ensure content has required collaboration fields
        required_fields = ['collaboration_type', 'participants', 'objective']
        for field in required_fields:
            if field not in self.content:
                raise ValueError(f"CollaborationRequestMessage requires '{field}' in content")


class StatusUpdateMessage(A2AMessage):
    """Specialized message for status updates."""
    
    message_type: Literal[MessageType.STATUS_UPDATE] = Field(default=MessageType.STATUS_UPDATE)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Ensure content has required status fields
        if 'status' not in self.content:
            raise ValueError("StatusUpdateMessage requires 'status' in content")


class CapabilityQueryMessage(A2AMessage):
    """Specialized message for capability queries."""
    
    message_type: Literal[MessageType.CAPABILITY_QUERY] = Field(default=MessageType.CAPABILITY_QUERY)


class CapabilityResponseMessage(A2AMessage):
    """Specialized message for capability responses."""
    
    message_type: Literal[MessageType.CAPABILITY_RESPONSE] = Field(default=MessageType.CAPABILITY_RESPONSE)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Ensure content has required capability fields
        if 'capabilities' not in self.content:
            raise ValueError("CapabilityResponseMessage requires 'capabilities' in content")


class HeartbeatMessage(A2AMessage):
    """Specialized message for heartbeat/health checks."""
    
    message_type: Literal[MessageType.HEARTBEAT] = Field(default=MessageType.HEARTBEAT)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Add default heartbeat content
        if not self.content:
            self.content = {
                "status": "alive",
                "timestamp": datetime.utcnow().isoformat()
            }


def create_message(
    message_type: MessageType,
    from_agent: str,
    to_agent: str,
    content: Dict[str, Any],
    **kwargs
) -> A2AMessage:
    """
    Factory function to create appropriate message types.
    """
    
    message_classes = {
        MessageType.TASK_REQUEST: TaskRequestMessage,
        MessageType.TASK_RESPONSE: TaskResponseMessage,
        MessageType.COLLABORATION_REQUEST: CollaborationRequestMessage,
        MessageType.STATUS_UPDATE: StatusUpdateMessage,
        MessageType.CAPABILITY_QUERY: CapabilityQueryMessage,
        MessageType.CAPABILITY_RESPONSE: CapabilityResponseMessage,
        MessageType.HEARTBEAT: HeartbeatMessage,
    }
    
    message_class = message_classes.get(message_type, A2AMessage)
    
    return message_class(
        message_type=message_type,
        from_agent=from_agent,
        to_agent=to_agent,
        content=content,
        **kwargs
    )


def create_task_request(
    from_agent: str,
    to_agent: str,
    task_description: str,
    context: Optional[Dict[str, Any]] = None,
    priority: MessagePriority = MessagePriority.NORMAL,
    **kwargs
) -> TaskRequestMessage:
    """Helper function to create task request messages."""
    
    content = {
        "task_description": task_description,
        "requested_at": datetime.utcnow().isoformat()
    }
    
    if context:
        content["context"] = context
    
    return TaskRequestMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        content=content,
        priority=priority,
        **kwargs
    )


def create_task_response(
    from_agent: str,
    to_agent: str,
    status: str,
    result: Optional[Any] = None,
    error: Optional[str] = None,
    correlation_id: Optional[str] = None,
    **kwargs
) -> TaskResponseMessage:
    """Helper function to create task response messages."""
    
    content = {
        "status": status,
        "completed_at": datetime.utcnow().isoformat()
    }
    
    if result is not None:
        content["result"] = result
    
    if error:
        content["error"] = error
    
    return TaskResponseMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        content=content,
        correlation_id=correlation_id,
        **kwargs
    )
