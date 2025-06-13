"""
Core TeamFactory class - orchestrates team creation.
"""

from pathlib import Path
from typing import Dict, List, Optional

from ..models import SubTeamRecommendation, TeamMember, TeamSpecification
from ..utils.constants import (
    DEPARTMENT_EXECUTIVE_MAPPING,
    MAX_TEAM_SIZE,
    MIN_TEAM_SIZE,
    PERSONALITY_TRAITS,
    SKEPTIC_THRESHOLD,
)


class TeamFactory:
    """Main factory class for creating AI teams."""

    def __init__(self):
        """Initialize the team factory."""
        self.generated_teams = []

    def analyze_request(
        self, description: str, framework: str, llm_provider: str
    ) -> Dict:
        """
        Analyze a team request using LLM.

        This is a placeholder for now - will be implemented with full LLM integration.
        """
        # TODO: Implement LLM analysis
        return {
            "team_name": "placeholder-team",
            "purpose": "Placeholder purpose",
            "members": [],
            "department": "engineering",
        }

    def create_team(self, spec: TeamSpecification) -> bool:
        """
        Create a team based on the specification.

        This is the main entry point for team creation.
        """
        # TODO: Implement full team creation
        self.generated_teams.append(spec)
        return True

    def validate_team_size(self, team_size: int) -> str:
        """Validate team size against constraints."""
        if team_size < MIN_TEAM_SIZE:
            return f"Team size ({team_size}) is below minimum ({MIN_TEAM_SIZE})"
        elif team_size > MAX_TEAM_SIZE:
            return f"Team size ({team_size}) exceeds maximum ({MAX_TEAM_SIZE})"
        else:
            return f"Team size ({team_size}) is within acceptable range"

    def should_add_skeptic(self, team_size: int) -> bool:
        """Determine if team should have a skeptic."""
        return team_size >= SKEPTIC_THRESHOLD

    def get_reporting_executive(self, department: str) -> str:
        """Get the executive a department reports to."""
        return DEPARTMENT_EXECUTIVE_MAPPING.get(department.lower(), "CEO")

    def get_personality_modifiers(self, personality: str) -> List[str]:
        """Get personality trait modifiers."""
        trait = PERSONALITY_TRAITS.get(personality, {})
        return trait.get("modifiers", [])
