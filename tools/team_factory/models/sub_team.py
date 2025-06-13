"""
Sub-team recommendation model.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class SubTeamRecommendation:
    """Recommendation for creating sub-teams under a parent team."""

    name: str
    purpose: str
    required_capabilities: List[str]
    rationale: str
    suggested_size: int = 5
    suggested_framework: str = "CrewAI"

    @property
    def directory_name(self) -> str:
        """Get directory-safe name for the sub-team."""
        return self.name.lower().replace(" ", "-").replace("_", "-")
