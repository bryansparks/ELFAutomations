"""
Conversation Manager for team chat sessions.

Manages the chat context, history, and delegation preparation.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..a2a import (
    ChatCoordinator,
    ChatDelegationReady,
    ChatMessage,
    ChatStatus,
    ChatStatusUpdate,
)
from .delegation_builder import DelegationBuilder, DelegationSpec

logger = logging.getLogger(__name__)


@dataclass
class ChatContext:
    """Context for a chat session."""

    session_id: str
    user_id: str
    team_id: str
    team_name: str
    manager_name: str
    manager_role: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    total_tokens: int = 0
    status: ChatStatus = ChatStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, tokens: int = 0):
        """Add a message to the conversation."""
        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "tokens": tokens,
            }
        )
        self.total_tokens += tokens

    def get_conversation_history(
        self, max_messages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history, optionally limited to recent messages."""
        if max_messages:
            return self.messages[-max_messages:]
        return self.messages

    def get_summary(self) -> str:
        """Generate a summary of the conversation."""
        # Simple summary - in production, use LLM for better summaries
        user_messages = [m for m in self.messages if m["role"] == "user"]
        assistant_messages = [m for m in self.messages if m["role"] == "assistant"]

        return (
            f"Chat session {self.session_id} between {self.user_id} and {self.manager_name}. "
            f"{len(user_messages)} user messages, {len(assistant_messages)} assistant responses. "
            f"Total tokens: {self.total_tokens}"
        )


class ConversationManager:
    """Manages chat conversations with team managers."""

    def __init__(
        self,
        team_agent,  # The team's manager agent (CrewAI or LangGraph)
        team_name: str,
        manager_name: str,
        manager_role: str,
        chat_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize conversation manager.

        Args:
            team_agent: The team's manager agent instance
            team_name: Name of the team
            manager_name: Name of the manager agent
            manager_role: Role of the manager agent
            chat_config: Chat configuration from team settings
        """
        self.team_agent = team_agent
        self.team_name = team_name
        self.manager_name = manager_name
        self.manager_role = manager_role
        self.chat_config = chat_config or {}

        # Active sessions
        self.sessions: Dict[str, ChatContext] = {}

        # Delegation readiness tracking
        self.delegation_ready: Dict[str, bool] = {}
        self.delegation_specs: Dict[str, Dict[str, Any]] = {}

        # Delegation builder for extracting task specs from conversations
        self.delegation_builder = DelegationBuilder()

    async def start_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:
        """
        Start a new chat session.

        Args:
            user_id: User identifier
            session_id: Optional session ID (generated if not provided)
            initial_context: Initial context for the conversation

        Returns:
            Tuple of (session_id, greeting_message)
        """
        session_id = session_id or str(uuid.uuid4())

        # Create session context
        context = ChatContext(
            session_id=session_id,
            user_id=user_id,
            team_id=self.team_name,
            team_name=self.team_name,
            manager_name=self.manager_name,
            manager_role=self.manager_role,
            metadata=initial_context or {},
        )

        self.sessions[session_id] = context
        self.delegation_ready[session_id] = False

        # Generate greeting
        greeting = self._generate_greeting(user_id, initial_context)
        context.add_message("assistant", greeting)

        logger.info(f"Started chat session {session_id} for user {user_id}")

        return session_id, greeting

    async def process_message(
        self,
        session_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message in the chat session.

        Args:
            session_id: Session identifier
            user_message: User's message
            context: Additional context for processing

        Returns:
            Response dictionary with assistant's reply and metadata
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        session.status = ChatStatus.THINKING

        # Add user message
        session.add_message("user", user_message, self._estimate_tokens(user_message))

        # Get conversation history for context
        history = session.get_conversation_history(
            max_messages=self.chat_config.get("context_window_messages", 20)
        )

        # Process with team agent
        start_time = datetime.utcnow()

        try:
            # Prepare prompt for the agent
            prompt = self._build_agent_prompt(history, user_message, context)

            # Get response from agent
            # This is where we'd integrate with CrewAI/LangGraph agent
            response = await self._get_agent_response(prompt, session)

            # Process response
            assistant_reply = response.get(
                "content", "I understand. Let me help you with that."
            )
            delegation_hint = response.get("delegation_ready", False)
            task_spec = response.get("task_specification")

            # Add assistant message
            session.add_message(
                "assistant", assistant_reply, self._estimate_tokens(assistant_reply)
            )

            # Check for delegation readiness
            # Analyze conversation after sufficient messages
            if len(session.messages) >= 4:  # At least 2 exchanges
                delegation_spec = self.delegation_builder.analyze_conversation(
                    messages=session.messages,
                    session_id=session_id,
                    user_id=session.user_id,
                )

                # Update readiness based on confidence
                if delegation_spec.confidence_level >= 0.7:
                    self.delegation_ready[session_id] = True
                    self.delegation_specs[session_id] = delegation_spec.to_dict()

                    # Add delegation hint to response if newly ready
                    if not delegation_hint and self.delegation_ready[session_id]:
                        assistant_reply += "\n\nI believe I have enough information to create a task for this. Would you like me to prepare a delegation for the team?"

            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()

            session.status = ChatStatus.WAITING_FOR_USER

            return {
                "response": assistant_reply,
                "thinking_time": response_time,
                "ready_to_delegate": self.delegation_ready[session_id],
                "message_count": len(session.messages),
                "total_tokens": session.total_tokens,
                "status": session.status.value,
            }

        except Exception as e:
            logger.error(f"Error processing message in session {session_id}: {e}")
            session.status = ChatStatus.ERROR
            raise

    def is_ready_to_delegate(self, session_id: str) -> bool:
        """Check if the manager is ready to delegate tasks."""
        return self.delegation_ready.get(session_id, False)

    def prepare_delegation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Prepare task delegation based on the conversation.

        Args:
            session_id: Session identifier

        Returns:
            Task specification ready for delegation
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

        # Use DelegationBuilder to analyze the conversation
        delegation_spec = self.delegation_builder.analyze_conversation(
            messages=session.messages, session_id=session_id, user_id=session.user_id
        )

        # Check if we have enough confidence to delegate
        if delegation_spec.confidence_level < 0.6:
            logger.info(
                f"Low confidence for delegation: {delegation_spec.confidence_level}"
            )
            return None

        # Mark as ready if confidence is high enough
        self.delegation_ready[session_id] = True

        # Store the spec
        self.delegation_specs[session_id] = delegation_spec.to_dict()

        return delegation_spec.to_dict()

    async def end_session(
        self, session_id: str, reason: str = "user_ended"
    ) -> Dict[str, Any]:
        """
        End a chat session.

        Args:
            session_id: Session identifier
            reason: Reason for ending the session

        Returns:
            Session summary
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        duration = (datetime.utcnow() - session.started_at).total_seconds()

        summary = {
            "session_id": session_id,
            "duration_seconds": duration,
            "total_messages": len(session.messages),
            "total_tokens": session.total_tokens,
            "delegation_created": self.delegation_ready.get(session_id, False),
            "end_reason": reason,
        }

        # Clean up
        del self.sessions[session_id]
        self.delegation_ready.pop(session_id, None)
        self.delegation_specs.pop(session_id, None)

        logger.info(f"Ended session {session_id}: {reason}")

        return summary

    def _generate_greeting(
        self, user_id: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate a greeting message for the user."""
        # In production, this would use the agent's personality
        return (
            f"Hello! I'm {self.manager_name}, the {self.manager_role} of {self.team_name}. "
            f"I'm here to help you with your request. What can I assist you with today?"
        )

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text."""
        # Simple estimation: ~4 characters per token
        return len(text) // 4

    def _build_agent_prompt(
        self,
        history: List[Dict[str, Any]],
        current_message: str,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build a prompt for the agent including conversation history."""
        # Format conversation history
        history_text = "\n".join(
            [
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in history[-10:]  # Last 10 messages
            ]
        )

        prompt = f"""You are {self.manager_name}, the {self.manager_role} of {self.team_name}.
You are having a conversation with a user to understand their needs before delegating tasks to your team.

Conversation so far:
{history_text}

Current message: {current_message}

Respond naturally and helpfully. If you have enough information to create a task for your team,
indicate this in your response metadata.

Remember to:
1. Be helpful and professional
2. Ask clarifying questions when needed
3. Summarize what you understand
4. Indicate when you're ready to create a task
"""

        if context:
            prompt += f"\nAdditional context: {json.dumps(context)}"

        return prompt

    async def _get_agent_response(
        self, prompt: str, session: ChatContext
    ) -> Dict[str, Any]:
        """
        Get response from the team agent.

        This is where we integrate with CrewAI/LangGraph agents.
        """
        # TODO: Integrate with actual agent
        # For now, return a mock response

        # Simulate thinking time
        import asyncio

        await asyncio.sleep(0.5)

        # Check if we have enough info to delegate
        message_count = len([m for m in session.messages if m["role"] == "user"])
        delegation_ready = message_count >= 3  # Simple heuristic

        response = {
            "content": "I understand your requirements. Let me process this information...",
            "delegation_ready": delegation_ready,
            "task_specification": None,
        }

        if delegation_ready:
            response["task_specification"] = {
                "title": "Task from chat session",
                "description": "Task created from chat conversation",
                "requirements": ["Requirement 1", "Requirement 2"],
                "priority": "normal",
                "estimated_hours": 8,
            }
            response["content"] = (
                "I have a clear understanding of what you need. "
                "I can create a task for my team to work on this. "
                "Would you like me to proceed with the delegation?"
            )

        return response
