"""
Shared tools available to all team members.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def team_communication(message: str, recipient: str = "all") -> str:
    """
    Send a message to team members.

    Args:
        message: The message to send
        recipient: Target recipient ("all" for broadcast)

    Returns:
        Confirmation of message sent
    """
    logger.info(f"Team communication to {recipient}: {message}")
    return f"Message sent to {recipient}: {message}"


@tool
def log_decision(decision: str, rationale: str, impact: str = "medium") -> str:
    """
    Log an important decision for team records.

    Args:
        decision: The decision made
        rationale: Why this decision was made
        impact: Impact level (low/medium/high)

    Returns:
        Confirmation of logged decision
    """
    logger.info(f"Decision logged: {decision} (Impact: {impact})")
    return f"Decision logged: {decision}"


@tool
def request_clarification(topic: str, from_whom: str) -> str:
    """
    Request clarification on a topic from a team member.

    Args:
        topic: What needs clarification
        from_whom: Who to ask for clarification

    Returns:
        Clarification request status
    """
    return f"Clarification requested from {from_whom} about: {topic}"
