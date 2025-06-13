"""
Team Factory - Automated AI Team Generation System

This package provides a comprehensive system for creating production-ready AI teams
with advanced capabilities including memory, learning, communication, and monitoring.
"""

__version__ = "2.0.0"

# Import main classes and functions for easy access
from .core.factory import TeamFactory
from .models.sub_team import SubTeamRecommendation
from .models.team_member import TeamMember
from .models.team_spec import TeamSpecification


# For backward compatibility
def main():
    """Run the team factory CLI."""
    from .cli import main as cli_main

    cli_main()


__all__ = [
    "TeamFactory",
    "TeamMember",
    "TeamSpecification",
    "SubTeamRecommendation",
    "main",
]
