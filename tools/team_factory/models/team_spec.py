"""
Team specification model.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .sub_team import SubTeamRecommendation
from .team_charter import TeamCharter
from .team_member import TeamMember


@dataclass
class TeamSpecification:
    """Complete specification for a team."""

    # Basic info
    name: str
    description: str
    purpose: str
    framework: str  # CrewAI or LangGraph

    # LLM configuration
    llm_provider: str  # OpenAI or Anthropic
    llm_model: str  # Specific model to use

    # Organization
    department: str
    reporting_to: Optional[str] = None  # Who this team reports to
    is_free_agent: bool = False  # Not tied to org structure

    # Chat interface configuration
    is_top_level: bool = False  # Marks team as top of organizational tree
    enable_chat_interface: bool = False  # Enable direct chat with manager
    chat_config: Dict[str, Any] = field(
        default_factory=lambda: {
            "allowed_roles": ["admin", "user"],
            "max_session_duration_minutes": 60,
            "max_messages_per_session": 100,
            "enable_delegation_preview": True,
            "context_window_messages": 20,
            "require_user_confirmation": True,
        }
    )

    # Team composition
    members: List[TeamMember] = field(default_factory=list)

    # Team charter
    charter: Optional[TeamCharter] = None

    # Communication patterns
    communication_pattern: Dict[str, List[str]] = field(default_factory=dict)
    a2a_capabilities: List[str] = field(default_factory=list)

    # Sub-teams
    sub_team_recommendations: List[SubTeamRecommendation] = field(default_factory=list)
    create_sub_teams: bool = False

    # Memory and evolution settings
    enable_memory: bool = True  # Use persistent memory system
    enable_evolution: bool = True  # Allow agents to evolve based on learnings
    enable_conversation_logging: bool = True  # Log all team communications
    memory_retention_days: int = 30  # How long to keep memories
    evolution_confidence_threshold: float = 0.9  # Min confidence for evolution
    improvement_cycle_frequency: str = "daily"  # daily, weekly, or manual

    # Validation
    size_validation: str = ""

    # Original request
    natural_language_description: str = ""

    def __post_init__(self):
        """Validate team specification."""
        # Ensure at least one manager
        if not any(m.is_manager for m in self.members):
            if self.members:
                self.members[0].is_manager = True

        # Validate team size
        team_size = len(self.members)
        if team_size < 2:
            self.size_validation = "Warning: Team has less than 2 members"
        elif team_size > 7:
            self.size_validation = (
                "Warning: Team has more than 7 members (Two-Pizza Rule)"
            )
        else:
            self.size_validation = f"Team size ({team_size}) is optimal"

    @property
    def directory_name(self) -> str:
        """Get directory-safe name for the team."""
        return self.name.lower().replace(" ", "-").replace("_", "-")

    @property
    def manager(self) -> Optional[TeamMember]:
        """Get the team manager."""
        for member in self.members:
            if member.is_manager:
                return member
        return None

    @property
    def has_skeptic(self) -> bool:
        """Check if team has a skeptic."""
        return any(m.is_skeptic or m.personality == "skeptic" for m in self.members)

    def get_process_type(self) -> str:
        """Determine the process type based on team size."""
        if self.framework == "CrewAI":
            return "hierarchical" if len(self.members) > 4 else "sequential"
        return "workflow"  # LangGraph uses workflow

    def validate_chat_config(self) -> bool:
        """Validate chat configuration settings."""
        if self.enable_chat_interface:
            # Only top-level teams can have chat interfaces
            if not self.is_top_level:
                self.enable_chat_interface = False
                return False

            # Must have a manager to chat with
            if not self.manager:
                self.enable_chat_interface = False
                return False

            # Ensure chat config has required fields
            required_fields = [
                "allowed_roles",
                "max_session_duration_minutes",
                "max_messages_per_session",
            ]
            for field in required_fields:
                if field not in self.chat_config:
                    return False

        return True
