#!/usr/bin/env python3
"""
Comprehensive Team Conversation Logging System
Captures all intra-team communications for analysis and improvement
"""

import asyncio
import json
import logging
import os
import queue
import threading
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Supabase integration
try:
    from utils.supabase_client import get_supabase_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase not available. Logging to files only.")


class MessageType(Enum):
    """Types of messages in team conversations"""

    PROPOSAL = "proposal"
    CHALLENGE = "challenge"
    DECISION = "decision"
    CLARIFICATION = "clarification"
    DELEGATION = "delegation"
    UPDATE = "update"
    QUESTION = "question"
    ANSWER = "answer"
    AGREEMENT = "agreement"
    DISAGREEMENT = "disagreement"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"


class ConversationLogger:
    """
    Centralized logging system for team conversations
    Logs to both local files and Supabase for analysis
    """

    def __init__(self, team_name: str, log_dir: str = "logs/conversations"):
        self.team_name = team_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Local file logging
        self.log_file = self.log_dir / f"{team_name}_conversations.jsonl"
        self.natural_log_file = self.log_dir / f"{team_name}_natural.log"

        # Structured logging queue for async Supabase writes
        self.log_queue = queue.Queue()
        self.supabase_client = None

        # Initialize Supabase if available
        if SUPABASE_AVAILABLE:
            try:
                self.supabase_client = get_supabase_client()
                # Start background thread for Supabase writes
                self.supabase_thread = threading.Thread(
                    target=self._supabase_writer, daemon=True
                )
                self.supabase_thread.start()
            except Exception as e:
                print(f"Failed to initialize Supabase: {e}")
                self.supabase_client = None

        # Performance metrics
        self.conversation_metrics = {
            "total_messages": 0,
            "messages_by_type": {},
            "messages_by_agent": {},
            "avg_response_time": 0,
            "decision_count": 0,
            "challenge_count": 0,
        }

        # Current conversation context
        self.current_task_id = None
        self.conversation_start = None

    def start_conversation(self, task_id: str, task_description: str):
        """Mark the start of a new conversation/task"""
        self.current_task_id = task_id
        self.conversation_start = datetime.utcnow()

        self.log_message(
            agent_name="system",
            message=f"Starting task: {task_description}",
            message_type=MessageType.UPDATE,
            metadata={"task_id": task_id, "task_description": task_description},
        )

    def end_conversation(self, outcome: str = "completed"):
        """Mark the end of a conversation/task"""
        if not self.current_task_id:
            return

        duration = (datetime.utcnow() - self.conversation_start).total_seconds()

        self.log_message(
            agent_name="system",
            message=f"Task completed: {outcome}",
            message_type=MessageType.UPDATE,
            metadata={
                "task_id": self.current_task_id,
                "outcome": outcome,
                "duration_seconds": duration,
            },
        )

        self.current_task_id = None
        self.conversation_start = None

    def log_message(
        self,
        agent_name: str,
        message: str,
        message_type: MessageType = MessageType.UPDATE,
        to_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a message from an agent

        Args:
            agent_name: Name of the agent sending the message
            message: The message content
            message_type: Type of message (proposal, challenge, etc.)
            to_agent: Target agent (if directed communication)
            metadata: Additional context (sentiment, confidence, etc.)
        """

        # Create structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "team_name": self.team_name,
            "task_id": self.current_task_id,
            "agent_name": agent_name,
            "message": message,
            "message_type": message_type.value,
            "to_agent": to_agent,
            "metadata": metadata or {},
        }

        # Add sentiment analysis placeholder
        if "sentiment" not in log_entry["metadata"]:
            log_entry["metadata"]["sentiment"] = self._analyze_sentiment(message)

        # Update metrics
        self._update_metrics(agent_name, message_type)

        # Write to local file (synchronous)
        self._write_to_file(log_entry)

        # Queue for Supabase (asynchronous)
        if self.supabase_client:
            self.log_queue.put(log_entry)

        # Write natural language version
        self._write_natural_log(agent_name, message, to_agent)

    def _write_to_file(self, log_entry: Dict):
        """Write structured log entry to JSONL file"""
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def _write_natural_log(
        self, agent_name: str, message: str, to_agent: Optional[str]
    ):
        """Write natural language log for human readability"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if to_agent:
            log_line = f"[{timestamp}] {agent_name} → {to_agent}: {message}\n"
        else:
            log_line = f"[{timestamp}] {agent_name}: {message}\n"

        with open(self.natural_log_file, "a") as f:
            f.write(log_line)

    def _supabase_writer(self):
        """Background thread to write logs to Supabase"""
        while True:
            try:
                # Get log entries from queue (blocking)
                log_entry = self.log_queue.get(timeout=1)

                # Write to Supabase
                self.supabase_client.table("team_conversations").insert(
                    {
                        "team_name": log_entry["team_name"],
                        "task_id": log_entry["task_id"],
                        "agent_name": log_entry["agent_name"],
                        "message": log_entry["message"],
                        "message_type": log_entry["message_type"],
                        "to_agent": log_entry["to_agent"],
                        "metadata": log_entry["metadata"],
                        "timestamp": log_entry["timestamp"],
                    }
                ).execute()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error writing to Supabase: {e}")
                # Could implement retry logic here

    def _analyze_sentiment(self, message: str) -> str:
        """Simple sentiment analysis (could be enhanced with NLP)"""
        positive_words = [
            "great",
            "excellent",
            "agree",
            "yes",
            "good",
            "perfect",
            "successful",
        ]
        negative_words = [
            "no",
            "problem",
            "issue",
            "disagree",
            "wrong",
            "fail",
            "concern",
        ]

        message_lower = message.lower()

        positive_score = sum(1 for word in positive_words if word in message_lower)
        negative_score = sum(1 for word in negative_words if word in message_lower)

        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        else:
            return "neutral"

    def _update_metrics(self, agent_name: str, message_type: MessageType):
        """Update conversation metrics"""
        self.conversation_metrics["total_messages"] += 1

        # Messages by type
        type_key = message_type.value
        if type_key not in self.conversation_metrics["messages_by_type"]:
            self.conversation_metrics["messages_by_type"][type_key] = 0
        self.conversation_metrics["messages_by_type"][type_key] += 1

        # Messages by agent
        if agent_name not in self.conversation_metrics["messages_by_agent"]:
            self.conversation_metrics["messages_by_agent"][agent_name] = 0
        self.conversation_metrics["messages_by_agent"][agent_name] += 1

        # Special counters
        if message_type == MessageType.DECISION:
            self.conversation_metrics["decision_count"] += 1
        elif message_type == MessageType.CHALLENGE:
            self.conversation_metrics["challenge_count"] += 1

    def get_metrics(self) -> Dict:
        """Get current conversation metrics"""
        return self.conversation_metrics.copy()

    def get_recent_conversations(self, limit: int = 100) -> List[Dict]:
        """Get recent conversations from local log"""
        conversations = []

        if self.log_file.exists():
            with open(self.log_file, "r") as f:
                # Read last N lines efficiently
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        conversations.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return conversations


class TeamLoggerMixin:
    """
    Mixin class for agents to add conversation logging capabilities
    Add this to any agent class to enable logging
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Extract team name from class or config
        team_name = getattr(self, "team_name", "unknown-team")
        self.conversation_logger = ConversationLogger(team_name)

        # Track last message time for response time metrics
        self.last_message_time = None

    def log_proposal(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a proposal message"""
        self.conversation_logger.log_message(
            agent_name=self.name,
            message=message,
            message_type=MessageType.PROPOSAL,
            to_agent=to_agent,
            metadata=metadata,
        )

    def log_challenge(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a challenge/skeptical message"""
        self.conversation_logger.log_message(
            agent_name=self.name,
            message=message,
            message_type=MessageType.CHALLENGE,
            to_agent=to_agent,
            metadata=metadata,
        )

    def log_decision(self, message: str, **metadata):
        """Log a decision message"""
        self.conversation_logger.log_message(
            agent_name=self.name,
            message=message,
            message_type=MessageType.DECISION,
            to_agent=None,  # Decisions are typically broadcast
            metadata=metadata,
        )

    def log_update(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a general update message"""
        self.conversation_logger.log_message(
            agent_name=self.name,
            message=message,
            message_type=MessageType.UPDATE,
            to_agent=to_agent,
            metadata=metadata,
        )

    @contextmanager
    def log_task(self, task_id: str, task_description: str):
        """Context manager for logging a complete task"""
        self.conversation_logger.start_conversation(task_id, task_description)
        try:
            yield
            self.conversation_logger.end_conversation("completed")
        except Exception as e:
            self.conversation_logger.end_conversation(f"failed: {str(e)}")
            raise


# Example integration with CrewAI agent
class LoggingCrewAIAgent:
    """Example of how to add logging to a CrewAI agent"""

    def __init__(self, name: str, team_name: str, *args, **kwargs):
        self.name = name
        self.team_name = team_name
        self.conversation_logger = ConversationLogger(team_name)
        # ... rest of CrewAI agent initialization

    def execute_task(self, task):
        """Execute a task with full conversation logging"""
        with self.conversation_logger.log_task(task.id, task.description):
            # Log initial thoughts
            self.conversation_logger.log_message(
                self.name,
                f"Starting analysis of task: {task.description}",
                MessageType.UPDATE,
            )

            # Simulate agent thinking and discussion
            self.conversation_logger.log_message(
                self.name,
                "I propose we approach this by first gathering market data",
                MessageType.PROPOSAL,
                to_agent="data_analyst",
            )

            # ... actual task execution

            # Log completion
            self.conversation_logger.log_message(
                self.name,
                "Task completed successfully with all objectives met",
                MessageType.DECISION,
            )


# Schema for Supabase tables
SUPABASE_SCHEMA = """
-- Team conversation logs
CREATE TABLE IF NOT EXISTS team_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_name TEXT NOT NULL,
    task_id TEXT,
    agent_name TEXT NOT NULL,
    message TEXT NOT NULL,
    message_type TEXT NOT NULL,
    to_agent TEXT,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_team_conversations_team ON team_conversations(team_name);
CREATE INDEX idx_team_conversations_task ON team_conversations(task_id);
CREATE INDEX idx_team_conversations_timestamp ON team_conversations(timestamp);
CREATE INDEX idx_team_conversations_type ON team_conversations(message_type);

-- View for conversation analysis
CREATE VIEW conversation_analytics AS
SELECT
    team_name,
    DATE(timestamp) as conversation_date,
    COUNT(*) as total_messages,
    COUNT(DISTINCT agent_name) as active_agents,
    COUNT(CASE WHEN message_type = 'decision' THEN 1 END) as decisions_made,
    COUNT(CASE WHEN message_type = 'challenge' THEN 1 END) as challenges_raised,
    AVG(CASE WHEN metadata->>'sentiment' = 'positive' THEN 1
             WHEN metadata->>'sentiment' = 'negative' THEN -1
             ELSE 0 END) as avg_sentiment
FROM team_conversations
GROUP BY team_name, DATE(timestamp);
"""


if __name__ == "__main__":
    # Example usage
    logger = ConversationLogger("marketing-team")

    # Simulate a team conversation
    with logger.log_task("TASK-001", "Create Q1 marketing campaign"):
        logger.log_message(
            "marketing_manager",
            "Team, we need to create our Q1 campaign",
            MessageType.UPDATE,
        )
        logger.log_message(
            "content_creator",
            "I propose focusing on video content",
            MessageType.PROPOSAL,
        )
        logger.log_message(
            "data_analyst",
            "Data shows 73% better engagement with video",
            MessageType.UPDATE,
        )
        logger.log_message(
            "skeptic",
            "What about production costs and timeline?",
            MessageType.CHALLENGE,
            to_agent="content_creator",
        )
        logger.log_message(
            "content_creator",
            "We can use AI tools to reduce costs by 60%",
            MessageType.ANSWER,
            to_agent="skeptic",
        )
        logger.log_message(
            "marketing_manager",
            "Approved. Let's proceed with video-first strategy",
            MessageType.DECISION,
        )

    # Display metrics
    print("\nConversation Metrics:")
    print(json.dumps(logger.get_metrics(), indent=2))

    # Show recent conversations
    print("\nRecent Conversations:")
    for conv in logger.get_recent_conversations(limit=5):
        print(f"[{conv['timestamp']}] {conv['agent_name']}: {conv['message']}")
