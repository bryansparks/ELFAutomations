"""Team Registry client for discovering and managing teams."""

from .client import Team, TeamHierarchy, TeamMember, TeamRegistryClient

__all__ = ["TeamRegistryClient", "Team", "TeamMember", "TeamHierarchy"]
