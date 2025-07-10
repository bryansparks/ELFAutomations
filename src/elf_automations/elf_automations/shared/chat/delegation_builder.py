"""
Delegation Builder for Chat Interface
Handles the preparation and validation of task delegations from chat conversations.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ...shared.a2a import ChatDelegationReady, TaskRequest
from ...shared.utils import get_logger

logger = get_logger(__name__)


class DelegationConfidence(Enum):
    """Confidence levels for delegation readiness."""

    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


class TaskPriority(Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class DelegationRequirement:
    """A single requirement extracted from conversation."""

    description: str
    source_message_id: Optional[str] = None
    confidence: float = 0.8
    category: Optional[str] = None  # technical, business, timeline, etc.


@dataclass
class DelegationSpec:
    """Complete specification for a delegated task."""

    # Core fields
    title: str
    description: str
    requirements: List[DelegationRequirement] = field(default_factory=list)

    # Task metadata
    priority: TaskPriority = TaskPriority.NORMAL
    estimated_hours: Optional[float] = None
    deadline: Optional[datetime] = None

    # Delegation metadata
    source: str = "chat_interface"
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    chat_summary: Optional[str] = None

    # Confidence and targeting
    confidence_level: float = 0.5
    suggested_teams: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)

    # Context from conversation
    key_decisions: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "description": self.description,
            "requirements": [
                {
                    "description": req.description,
                    "confidence": req.confidence,
                    "category": req.category,
                }
                for req in self.requirements
            ],
            "priority": self.priority.value,
            "estimated_hours": self.estimated_hours,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "source": self.source,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "chat_summary": self.chat_summary,
            "confidence_level": self.confidence_level,
            "suggested_teams": self.suggested_teams,
            "required_skills": self.required_skills,
            "key_decisions": self.key_decisions,
            "constraints": self.constraints,
            "success_criteria": self.success_criteria,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_task_request(self, from_agent: str, to_agent: str) -> TaskRequest:
        """Convert to A2A TaskRequest."""
        return TaskRequest(
            from_agent=from_agent,
            to_agent=to_agent,
            task_type="delegated_from_chat",
            task_description=self.description,
            context={
                "delegation_spec": self.to_dict(),
                "requirements": [req.description for req in self.requirements],
                "priority": self.priority.value,
                "deadline": self.deadline.isoformat() if self.deadline else None,
                "success_criteria": self.success_criteria,
                "constraints": self.constraints,
            },
            timeout=int(self.estimated_hours * 3600) if self.estimated_hours else 3600,
        )


class DelegationBuilder:
    """Builds task delegations from chat conversations."""

    def __init__(self):
        self.specs: Dict[str, DelegationSpec] = {}

        # Keywords for extraction
        self.requirement_keywords = [
            "need",
            "require",
            "must",
            "should",
            "want",
            "expect",
            "ensure",
            "make sure",
            "important",
            "critical",
            "essential",
        ]

        self.timeline_keywords = [
            "by",
            "before",
            "deadline",
            "due",
            "within",
            "asap",
            "urgent",
            "immediately",
            "today",
            "tomorrow",
            "week",
            "month",
        ]

        self.priority_indicators = {
            TaskPriority.URGENT: [
                "urgent",
                "asap",
                "immediately",
                "critical",
                "emergency",
            ],
            TaskPriority.HIGH: ["important", "high priority", "soon", "quickly"],
            TaskPriority.NORMAL: ["normal", "regular", "standard", "when you can"],
            TaskPriority.LOW: [
                "low priority",
                "nice to have",
                "optional",
                "if possible",
            ],
        }

    def analyze_conversation(
        self,
        messages: List[Dict[str, Any]],
        session_id: str,
        user_id: Optional[str] = None,
    ) -> DelegationSpec:
        """
        Analyze a conversation and build a delegation spec.

        Args:
            messages: List of chat messages with role, content, timestamp
            session_id: Current session ID
            user_id: User ID if available

        Returns:
            DelegationSpec with extracted information
        """
        # Initialize spec
        spec = DelegationSpec(
            title="Task from chat conversation",
            description="",
            session_id=session_id,
            user_id=user_id,
        )

        # Extract information from messages
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        if user_messages:
            # Extract title from first substantial user message
            spec.title = self._extract_title(user_messages)

            # Build description from user intent
            spec.description = self._build_description(user_messages)

            # Extract requirements
            spec.requirements = self._extract_requirements(messages)

            # Determine priority
            spec.priority = self._determine_priority(user_messages)

            # Extract timeline/deadline
            spec.deadline = self._extract_deadline(user_messages)

            # Extract constraints and success criteria
            spec.constraints = self._extract_constraints(messages)
            spec.success_criteria = self._extract_success_criteria(messages)

            # Estimate effort
            spec.estimated_hours = self._estimate_effort(spec)

            # Suggest teams based on content
            spec.suggested_teams = self._suggest_teams(spec)

            # Calculate confidence
            spec.confidence_level = self._calculate_confidence(spec, messages)

            # Generate summary
            spec.chat_summary = self._generate_summary(messages)

        # Store the spec
        self.specs[session_id] = spec

        return spec

    def _extract_title(self, user_messages: List[Dict[str, Any]]) -> str:
        """Extract a concise title from user messages."""
        # Look for explicit task statements
        for msg in user_messages:
            content = msg.get("content", "").lower()

            # Check for explicit task phrases
            if "i need" in content or "please" in content or "can you" in content:
                # Extract the main request
                lines = msg["content"].split("\n")
                for line in lines:
                    if any(
                        keyword in line.lower()
                        for keyword in ["need", "want", "please", "help"]
                    ):
                        # Clean and truncate
                        title = line.strip()
                        title = re.sub(
                            r"^(i need|please|can you|help me|i want)\s+",
                            "",
                            title,
                            flags=re.IGNORECASE,
                        )
                        return title[:100]  # Max 100 chars

        # Fallback: use first message snippet
        if user_messages:
            first_msg = user_messages[0].get("content", "")
            return first_msg[:100].strip() + ("..." if len(first_msg) > 100 else "")

        return "Task from chat conversation"

    def _build_description(self, user_messages: List[Dict[str, Any]]) -> str:
        """Build a comprehensive description from user messages."""
        description_parts = []

        for msg in user_messages:
            content = msg.get("content", "")
            # Skip very short messages
            if len(content) < 20:
                continue

            # Add substantial messages to description
            description_parts.append(content)

        # Join with proper spacing
        full_description = "\n\n".join(description_parts)

        # Add context prefix
        return f"User request from chat session:\n\n{full_description}"

    def _extract_requirements(
        self, messages: List[Dict[str, Any]]
    ) -> List[DelegationRequirement]:
        """Extract specific requirements from messages."""
        requirements = []

        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")

            # Look for requirement patterns
            lines = content.split("\n")
            for line in lines:
                line_lower = line.lower()

                # Check for requirement keywords
                if any(keyword in line_lower for keyword in self.requirement_keywords):
                    # Extract the requirement
                    req_text = line.strip()

                    # Determine category
                    category = None
                    if any(
                        word in line_lower
                        for word in ["api", "database", "code", "technical"]
                    ):
                        category = "technical"
                    elif any(
                        word in line_lower for word in ["user", "customer", "business"]
                    ):
                        category = "business"
                    elif any(
                        word in line_lower for word in ["deadline", "timeline", "when"]
                    ):
                        category = "timeline"

                    # Higher confidence for user requirements
                    confidence = 0.9 if role == "user" else 0.7

                    requirements.append(
                        DelegationRequirement(
                            description=req_text,
                            source_message_id=msg.get("id"),
                            confidence=confidence,
                            category=category,
                        )
                    )

        # Remove duplicates
        seen = set()
        unique_requirements = []
        for req in requirements:
            if req.description not in seen:
                seen.add(req.description)
                unique_requirements.append(req)

        return unique_requirements

    def _determine_priority(self, user_messages: List[Dict[str, Any]]) -> TaskPriority:
        """Determine task priority from conversation."""
        all_content = " ".join(msg.get("content", "").lower() for msg in user_messages)

        # Check priority indicators
        for priority, keywords in self.priority_indicators.items():
            if any(keyword in all_content for keyword in keywords):
                return priority

        return TaskPriority.NORMAL

    def _extract_deadline(
        self, user_messages: List[Dict[str, Any]]
    ) -> Optional[datetime]:
        """Extract deadline from messages."""
        # This is a simplified implementation
        # In production, you'd use date parsing libraries

        for msg in user_messages:
            content = msg.get("content", "").lower()

            if any(keyword in content for keyword in self.timeline_keywords):
                # Simple patterns
                if "today" in content:
                    return datetime.utcnow().replace(hour=23, minute=59)
                elif "tomorrow" in content:
                    from datetime import timedelta

                    return datetime.utcnow() + timedelta(days=1)
                # Add more sophisticated date parsing here

        return None

    def _extract_constraints(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract constraints from conversation."""
        constraints = []
        constraint_keywords = [
            "cannot",
            "must not",
            "avoid",
            "don't",
            "shouldn't",
            "constraint",
            "limitation",
        ]

        for msg in messages:
            content = msg.get("content", "")
            lines = content.split("\n")

            for line in lines:
                if any(keyword in line.lower() for keyword in constraint_keywords):
                    constraints.append(line.strip())

        return constraints

    def _extract_success_criteria(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract success criteria from conversation."""
        criteria = []
        success_keywords = [
            "success",
            "complete when",
            "done when",
            "finished when",
            "goal",
            "outcome",
        ]

        for msg in messages:
            content = msg.get("content", "")
            lines = content.split("\n")

            for line in lines:
                if any(keyword in line.lower() for keyword in success_keywords):
                    criteria.append(line.strip())

        return criteria

    def _estimate_effort(self, spec: DelegationSpec) -> float:
        """Estimate effort in hours based on requirements and complexity."""
        base_hours = 4.0  # Base estimate

        # Add hours based on requirements
        hours = base_hours + (len(spec.requirements) * 0.5)

        # Adjust for priority
        if spec.priority == TaskPriority.URGENT:
            hours *= 0.8  # Rushed work
        elif spec.priority == TaskPriority.LOW:
            hours *= 1.2  # More relaxed timeline

        # Cap at reasonable limits
        return min(max(hours, 1.0), 80.0)

    def _suggest_teams(self, spec: DelegationSpec) -> List[str]:
        """Suggest teams based on task content."""
        suggestions = []

        content = (spec.title + " " + spec.description).lower()

        # Simple keyword matching
        team_keywords = {
            "engineering-team": [
                "code",
                "api",
                "database",
                "technical",
                "develop",
                "implement",
            ],
            "marketing-team": ["campaign", "marketing", "social", "content", "brand"],
            "operations-team": [
                "process",
                "operations",
                "deployment",
                "infrastructure",
            ],
            "finance-team": ["budget", "cost", "financial", "accounting", "expense"],
            "product-team": [
                "feature",
                "product",
                "user experience",
                "requirements",
                "design",
            ],
        }

        for team, keywords in team_keywords.items():
            if any(keyword in content for keyword in keywords):
                suggestions.append(team)

        # Default to general team if no specific match
        if not suggestions:
            suggestions.append("general-team")

        return suggestions

    def _calculate_confidence(
        self, spec: DelegationSpec, messages: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence level for delegation readiness."""
        confidence = 0.5  # Base confidence

        # Increase confidence based on clarity indicators
        if spec.title != "Task from chat conversation":
            confidence += 0.1

        if len(spec.requirements) > 0:
            confidence += min(len(spec.requirements) * 0.05, 0.2)

        if spec.success_criteria:
            confidence += 0.1

        if len(messages) > 5:  # Substantial conversation
            confidence += 0.1

        # Cap at maximum
        return min(confidence, 0.95)

    def _generate_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a summary of the conversation."""
        # In production, this could use an LLM for better summaries

        user_intents = []
        key_points = []

        for msg in messages:
            if msg.get("role") == "user":
                # First line often contains main intent
                lines = msg.get("content", "").split("\n")
                if lines and lines[0]:
                    user_intents.append(lines[0][:100])
            elif msg.get("role") == "assistant":
                # Look for clarifications or confirmations
                content = msg.get("content", "")
                if "will" in content.lower() or "plan to" in content.lower():
                    key_points.append(content[:100])

        summary_parts = []

        if user_intents:
            summary_parts.append(f"User requested: {'; '.join(user_intents[:3])}")

        if key_points:
            summary_parts.append(f"Agreed approach: {'; '.join(key_points[:2])}")

        return (
            " | ".join(summary_parts)
            if summary_parts
            else "Chat conversation about task delegation"
        )

    def prepare_delegation_message(self, spec: DelegationSpec) -> ChatDelegationReady:
        """Create a ChatDelegationReady message from a delegation spec."""
        return ChatDelegationReady(
            session_id=spec.session_id or "",
            task_specification=spec.to_dict(),
            chat_summary=spec.chat_summary or "",
            confidence_level=spec.confidence_level,
            suggested_teams=spec.suggested_teams,
            estimated_effort=f"{spec.estimated_hours:.1f} hours"
            if spec.estimated_hours
            else None,
            requires_user_confirmation=True,
        )

    def update_spec_with_modifications(
        self, session_id: str, modifications: Dict[str, Any]
    ) -> Optional[DelegationSpec]:
        """Update a delegation spec with user modifications."""
        spec = self.specs.get(session_id)
        if not spec:
            return None

        # Update fields based on modifications
        if "title" in modifications:
            spec.title = modifications["title"]

        if "description" in modifications:
            spec.description = modifications["description"]

        if "priority" in modifications:
            try:
                spec.priority = TaskPriority(modifications["priority"])
            except ValueError:
                logger.warning(f"Invalid priority value: {modifications['priority']}")

        if "deadline" in modifications:
            # Parse deadline (simplified)
            spec.deadline = modifications["deadline"]

        if "requirements" in modifications:
            # Add new requirements
            for req_text in modifications["requirements"]:
                spec.requirements.append(
                    DelegationRequirement(
                        description=req_text,
                        confidence=0.95,  # High confidence for user-added requirements
                    )
                )

        if "suggested_teams" in modifications:
            spec.suggested_teams = modifications["suggested_teams"]

        # Update timestamp
        spec.updated_at = datetime.utcnow()

        return spec
