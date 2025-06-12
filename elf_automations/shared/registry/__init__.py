"""Team Registry client for discovering and managing teams."""

from .client import TeamRegistryClient, Team, TeamMember, TeamHierarchy

__all__ = ['TeamRegistryClient', 'Team', 'TeamMember', 'TeamHierarchy']