"""Team Registry Client for discovering and managing teams.

This client provides a high-level interface to the Team Registry MCP server,
enabling teams to:
- Discover other teams by capability or department
- Query organizational hierarchy
- Register themselves and update status
- Find appropriate teams for delegation
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set

from ..mcp.client import MCPClient
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TeamMember:
    """Represents a member of a team."""

    agent_name: str
    role: str
    capabilities: List[str]
    is_manager: bool = False


@dataclass
class Team:
    """Represents a team in the organization."""

    id: str
    name: str
    type: str
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    members: List[TeamMember] = field(default_factory=list)

    @property
    def capabilities(self) -> Set[str]:
        """Get all unique capabilities across team members."""
        caps = set()
        for member in self.members:
            caps.update(member.capabilities)
        return caps

    @property
    def manager(self) -> Optional[TeamMember]:
        """Get the team manager if one exists."""
        for member in self.members:
            if member.is_manager:
                return member
        return None


@dataclass
class TeamHierarchy:
    """Represents a team's place in the organizational hierarchy."""

    team: Team
    parent: Optional[Team] = None
    children: List[Team] = field(default_factory=list)

    def get_all_descendants(self) -> List[Team]:
        """Get all descendant teams recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            # In real implementation, would need to fetch child hierarchies
        return descendants


class TeamRegistryClient:
    """Client for interacting with the Team Registry MCP server.

    This client provides high-level methods for team discovery,
    registration, and management through the MCP interface.
    """

    def __init__(self, mcp_client: Optional[MCPClient] = None):
        """Initialize the registry client.

        Args:
            mcp_client: Optional MCPClient instance. If not provided, creates one.
        """
        self.mcp_client = mcp_client or MCPClient()
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes

    async def register_team(
        self,
        name: str,
        type: str,
        parent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Team:
        """Register a new team in the registry.

        Args:
            name: Team name
            type: Team type (e.g., 'engineering', 'marketing')
            parent_name: Parent team name for hierarchy
            metadata: Additional team metadata

        Returns:
            The registered Team object
        """
        try:
            result = await self.mcp_client.call_tool_async(
                "team-registry",
                "register_team",
                {
                    "name": name,
                    "type": type,
                    "parent_name": parent_name,
                    "metadata": metadata or {},
                },
            )

            if result.get("success"):
                team_data = result.get("team", {})
                return Team(
                    id=team_data.get("id"),
                    name=team_data.get("name"),
                    type=team_data.get("type"),
                    parent_id=team_data.get("parent_id"),
                    metadata=team_data.get("metadata", {}),
                )
            else:
                raise Exception(f"Failed to register team: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error registering team {name}: {e}")
            raise

    async def add_team_member(
        self,
        team_name: str,
        agent_name: str,
        role: str,
        capabilities: List[str],
        is_manager: bool = False,
    ) -> bool:
        """Add a member to a team.

        Args:
            team_name: Name of the team
            agent_name: Name of the agent
            role: Agent's role in the team
            capabilities: List of agent capabilities
            is_manager: Whether this agent is the team manager

        Returns:
            True if successful
        """
        try:
            result = await self.mcp_client.call_tool_async(
                "team-registry",
                "add_team_member",
                {
                    "team_name": team_name,
                    "agent_name": agent_name,
                    "role": role,
                    "capabilities": capabilities,
                    "is_manager": is_manager,
                },
            )

            return result.get("success", False)

        except Exception as e:
            logger.error(f"Error adding member to team {team_name}: {e}")
            return False

    async def find_teams_by_capability(self, capability: str) -> List[Team]:
        """Find teams that have a specific capability.

        Args:
            capability: The capability to search for

        Returns:
            List of teams with the capability
        """
        cache_key = f"capability:{capability}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            result = await self.mcp_client.call_tool_async(
                "team-registry", "query_teams", {"capability": capability}
            )

            teams = []
            if result.get("success"):
                for team_data in result.get("teams", []):
                    team = await self._build_team_with_members(team_data)
                    teams.append(team)

            self._cache[cache_key] = teams
            return teams

        except Exception as e:
            logger.error(f"Error finding teams by capability {capability}: {e}")
            return []

    async def find_teams_by_type(self, team_type: str) -> List[Team]:
        """Find teams of a specific type.

        Args:
            team_type: The team type (e.g., 'engineering', 'marketing')

        Returns:
            List of teams of that type
        """
        try:
            result = await self.mcp_client.call_tool_async(
                "team-registry", "query_teams", {"type": team_type}
            )

            teams = []
            if result.get("success"):
                for team_data in result.get("teams", []):
                    team = await self._build_team_with_members(team_data)
                    teams.append(team)

            return teams

        except Exception as e:
            logger.error(f"Error finding teams by type {team_type}: {e}")
            return []

    async def get_team_hierarchy(self, team_name: str) -> Optional[TeamHierarchy]:
        """Get the organizational hierarchy for a team.

        Args:
            team_name: Name of the team

        Returns:
            TeamHierarchy object with parent and children
        """
        try:
            result = await self.mcp_client.call_tool_async(
                "team-registry", "get_team_hierarchy", {"team_name": team_name}
            )

            if result.get("success"):
                hierarchy_data = result.get("hierarchy", {})

                # Build team objects
                team = await self._build_team_with_members(
                    hierarchy_data.get("team", {})
                )
                parent = None
                if hierarchy_data.get("parent"):
                    parent = await self._build_team_with_members(
                        hierarchy_data["parent"]
                    )

                children = []
                for child_data in hierarchy_data.get("children", []):
                    child = await self._build_team_with_members(child_data)
                    children.append(child)

                return TeamHierarchy(team=team, parent=parent, children=children)

            return None

        except Exception as e:
            logger.error(f"Error getting hierarchy for team {team_name}: {e}")
            return None

    async def get_executive_teams(self, executive_name: str) -> List[Team]:
        """Get all teams reporting to a specific executive.

        Args:
            executive_name: Name of the executive (e.g., 'chief_technology_officer')

        Returns:
            List of teams reporting to that executive
        """
        try:
            result = await self.mcp_client.call_tool_async(
                "team-registry",
                "get_executive_teams",
                {"executive_name": executive_name},
            )

            teams = []
            if result.get("success"):
                for team_data in result.get("teams", []):
                    team = await self._build_team_with_members(team_data)
                    teams.append(team)

            return teams

        except Exception as e:
            logger.error(f"Error getting teams for executive {executive_name}: {e}")
            return []

    async def update_team_capabilities(
        self, team_name: str, agent_name: str, capabilities: List[str]
    ) -> bool:
        """Update the capabilities of a team member.

        Args:
            team_name: Name of the team
            agent_name: Name of the agent
            capabilities: New list of capabilities

        Returns:
            True if successful
        """
        # This would need a new MCP tool to be fully implemented
        # For now, we can update by re-adding the member
        logger.info(f"Updating capabilities for {agent_name} in {team_name}")
        # Implementation would go here
        return True

    async def find_collaborators(self, required_capabilities: List[str]) -> List[Team]:
        """Find teams that collectively have all required capabilities.

        Args:
            required_capabilities: List of required capabilities

        Returns:
            List of teams that together have all capabilities
        """
        teams_by_capability = {}

        # Find teams for each capability
        for cap in required_capabilities:
            teams = await self.find_teams_by_capability(cap)
            teams_by_capability[cap] = teams

        # Find minimal set of teams that cover all capabilities
        # Simple implementation: return all unique teams
        all_teams = {}
        for teams in teams_by_capability.values():
            for team in teams:
                all_teams[team.name] = team

        return list(all_teams.values())

    async def _build_team_with_members(self, team_data: Dict[str, Any]) -> Team:
        """Build a Team object with its members.

        Args:
            team_data: Raw team data from MCP

        Returns:
            Team object with members populated
        """
        team = Team(
            id=team_data.get("id", ""),
            name=team_data.get("name", ""),
            type=team_data.get("type", ""),
            parent_id=team_data.get("parent_id"),
            metadata=team_data.get("metadata", {}),
        )

        # Get team members if not included
        if not team_data.get("members"):
            try:
                result = await self.mcp_client.call_tool_async(
                    "team-registry", "get_team_members", {"team_name": team.name}
                )

                if result.get("success"):
                    members_data = result.get("members", [])
                    for member_data in members_data:
                        member = TeamMember(
                            agent_name=member_data.get("agent_name", ""),
                            role=member_data.get("role", ""),
                            capabilities=member_data.get("capabilities", []),
                            is_manager=member_data.get("is_manager", False),
                        )
                        team.members.append(member)
            except Exception as e:
                logger.warning(f"Could not fetch members for team {team.name}: {e}")

        return team

    # Synchronous convenience methods
    def register_team_sync(
        self,
        name: str,
        type: str,
        parent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Team:
        """Synchronous version of register_team."""
        return asyncio.run(self.register_team(name, type, parent_name, metadata))

    def find_teams_by_capability_sync(self, capability: str) -> List[Team]:
        """Synchronous version of find_teams_by_capability."""
        return asyncio.run(self.find_teams_by_capability(capability))

    def find_teams_by_type_sync(self, team_type: str) -> List[Team]:
        """Synchronous version of find_teams_by_type."""
        return asyncio.run(self.find_teams_by_type(team_type))

    def get_team_hierarchy_sync(self, team_name: str) -> Optional[TeamHierarchy]:
        """Synchronous version of get_team_hierarchy."""
        return asyncio.run(self.get_team_hierarchy(team_name))

    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
        logger.info("Registry client cache cleared")
