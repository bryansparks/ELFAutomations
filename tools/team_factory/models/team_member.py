"""
Team member model definition.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TeamMember:
    """Represents a single team member with all their attributes."""

    # Core attributes
    name: str
    role: str
    responsibilities: List[str]
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)

    # Personality and behavior
    personality: str = "collaborator"  # Default personality trait
    personality_traits: List[str] = field(default_factory=list)

    # Communication patterns
    communicates_with: List[str] = field(default_factory=list)  # Intra-team
    manages_teams: List[str] = field(default_factory=list)  # Inter-team A2A

    # Role flags
    is_manager: bool = False
    is_skeptic: bool = False

    # Generated attributes
    system_prompt: Optional[str] = None

    def __post_init__(self):
        """Validate and set defaults after initialization."""
        # Ensure personality is in traits list
        if self.personality and self.personality not in self.personality_traits:
            self.personality_traits.append(self.personality)

        # Mark skeptics
        if self.personality == "skeptic":
            self.is_skeptic = True

    @property
    def filename_safe_name(self) -> str:
        """Get a filename-safe version of the member name."""
        return self.name.lower().replace(" ", "_").replace("-", "_")

    @property
    def class_name(self) -> str:
        """Get a class-name version of the member name."""
        return "".join(word.capitalize() for word in self.name.split())

    def has_a2a_capabilities(self) -> bool:
        """Check if this member needs A2A capabilities."""
        return self.is_manager or bool(self.manages_teams)
