"""Registry tools for CrewAI agents to discover and interact with other teams.

These tools enable agents to:
- Find teams by capability or type
- Discover organizational hierarchy
- Locate appropriate collaborators
- Update team status
"""

import json
from typing import List, Dict, Any, Optional
from crewai_tools import BaseTool

from ..registry.client import TeamRegistryClient, Team, TeamHierarchy
from ..utils.logging import get_logger

logger = get_logger(__name__)


class FindTeamByCapabilityTool(BaseTool):
    """Tool for finding teams with specific capabilities."""
    
    name: str = "find_team_by_capability"
    description: str = (
        "Find teams that have a specific capability or skill. "
        "Use this when you need to delegate work or find collaborators. "
        "Input should be a capability like 'marketing', 'database_design', 'frontend_development'."
    )
    
    def __init__(self, registry_client: TeamRegistryClient):
        super().__init__()
        self.registry_client = registry_client
    
    def _run(self, capability: str) -> str:
        """Find teams with the specified capability."""
        try:
            teams = self.registry_client.find_teams_by_capability_sync(capability)
            
            if not teams:
                return f"No teams found with capability '{capability}'"
            
            result = f"Found {len(teams)} team(s) with capability '{capability}':\n\n"
            
            for team in teams:
                result += f"Team: {team.name} (Type: {team.type})\n"
                result += f"  Capabilities: {', '.join(team.capabilities)}\n"
                
                # Find which members have this capability
                members_with_cap = [
                    m for m in team.members 
                    if capability in m.capabilities
                ]
                
                if members_with_cap:
                    result += f"  Members with this capability:\n"
                    for member in members_with_cap:
                        result += f"    - {member.agent_name} ({member.role})\n"
                
                if team.manager:
                    result += f"  Manager: {team.manager.agent_name}\n"
                    
                result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding teams by capability: {e}")
            return f"Error searching for teams: {str(e)}"


class FindTeamByTypeTool(BaseTool):
    """Tool for finding teams of a specific type."""
    
    name: str = "find_team_by_type"
    description: str = (
        "Find all teams of a specific type or department. "
        "Use this to discover teams in engineering, marketing, sales, etc. "
        "Input should be a team type like 'engineering', 'marketing', 'executive'."
    )
    
    def __init__(self, registry_client: TeamRegistryClient):
        super().__init__()
        self.registry_client = registry_client
    
    def _run(self, team_type: str) -> str:
        """Find teams of the specified type."""
        try:
            teams = self.registry_client.find_teams_by_type_sync(team_type)
            
            if not teams:
                return f"No teams found of type '{team_type}'"
            
            result = f"Found {len(teams)} {team_type} team(s):\n\n"
            
            for team in teams:
                result += f"Team: {team.name}\n"
                result += f"  Members: {len(team.members)}\n"
                result += f"  Capabilities: {', '.join(list(team.capabilities)[:5])}"
                
                if len(team.capabilities) > 5:
                    result += f" (and {len(team.capabilities) - 5} more)"
                result += "\n"
                
                if team.manager:
                    result += f"  Manager: {team.manager.agent_name}\n"
                    
                result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding teams by type: {e}")
            return f"Error searching for teams: {str(e)}"


class GetTeamHierarchyTool(BaseTool):
    """Tool for understanding team organizational structure."""
    
    name: str = "get_team_hierarchy"
    description: str = (
        "Get the organizational hierarchy for a team, including parent and child teams. "
        "Use this to understand reporting structure and delegation paths. "
        "Input should be a team name."
    )
    
    def __init__(self, registry_client: TeamRegistryClient):
        super().__init__()
        self.registry_client = registry_client
    
    def _run(self, team_name: str) -> str:
        """Get hierarchy for the specified team."""
        try:
            hierarchy = self.registry_client.get_team_hierarchy_sync(team_name)
            
            if not hierarchy:
                return f"Team '{team_name}' not found in registry"
            
            result = f"Organizational Hierarchy for {team_name}:\n\n"
            
            # Current team
            result += f"Team: {hierarchy.team.name} (Type: {hierarchy.team.type})\n"
            result += f"  Members: {len(hierarchy.team.members)}\n"
            result += f"  Manager: {hierarchy.team.manager.agent_name if hierarchy.team.manager else 'None'}\n\n"
            
            # Parent
            if hierarchy.parent:
                result += f"Reports to: {hierarchy.parent.name}\n"
                result += f"  Parent Manager: {hierarchy.parent.manager.agent_name if hierarchy.parent.manager else 'None'}\n\n"
            else:
                result += "Reports to: None (Top-level team)\n\n"
            
            # Children
            if hierarchy.children:
                result += f"Subordinate Teams ({len(hierarchy.children)}):\n"
                for child in hierarchy.children:
                    result += f"  - {child.name} (Type: {child.type})\n"
                    if child.manager:
                        result += f"    Manager: {child.manager.agent_name}\n"
            else:
                result += "No subordinate teams\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting team hierarchy: {e}")
            return f"Error retrieving hierarchy: {str(e)}"


class FindCollaboratorsTool(BaseTool):
    """Tool for finding teams that can collaborate on complex tasks."""
    
    name: str = "find_collaborators"
    description: str = (
        "Find teams that collectively have all required capabilities for a complex task. "
        "Use this when a task requires multiple skills across different teams. "
        "Input should be a JSON array of required capabilities, e.g., "
        '["frontend_development", "database_design", "marketing"]'
    )
    
    def __init__(self, registry_client: TeamRegistryClient):
        super().__init__()
        self.registry_client = registry_client
    
    def _run(self, capabilities_json: str) -> str:
        """Find collaborators for the specified capabilities."""
        try:
            # Parse the JSON input
            try:
                required_capabilities = json.loads(capabilities_json)
                if not isinstance(required_capabilities, list):
                    return "Input must be a JSON array of capabilities"
            except json.JSONDecodeError:
                return "Invalid JSON. Please provide a JSON array of capabilities."
            
            # Find collaborators
            teams = self.registry_client.find_collaborators_sync(required_capabilities)
            
            if not teams:
                return f"No teams found with the required capabilities: {', '.join(required_capabilities)}"
            
            result = f"Found {len(teams)} team(s) for collaboration:\n\n"
            
            # Show which capabilities each team provides
            capability_coverage = {}
            for cap in required_capabilities:
                capability_coverage[cap] = []
            
            for team in teams:
                result += f"Team: {team.name} (Type: {team.type})\n"
                result += f"  Manager: {team.manager.agent_name if team.manager else 'None'}\n"
                result += "  Provides capabilities:\n"
                
                team_caps = []
                for cap in required_capabilities:
                    if cap in team.capabilities:
                        team_caps.append(cap)
                        capability_coverage[cap].append(team.name)
                
                for cap in team_caps:
                    result += f"    - {cap}\n"
                result += "\n"
            
            # Summary of coverage
            result += "Capability Coverage Summary:\n"
            for cap, teams_with_cap in capability_coverage.items():
                if teams_with_cap:
                    result += f"  ✓ {cap}: {', '.join(teams_with_cap)}\n"
                else:
                    result += f"  ✗ {cap}: No team found\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding collaborators: {e}")
            return f"Error searching for collaborators: {str(e)}"


class GetExecutiveTeamsTool(BaseTool):
    """Tool for finding teams under a specific executive."""
    
    name: str = "get_executive_teams"
    description: str = (
        "Get all teams reporting to a specific executive. "
        "Use this to understand executive span of control. "
        "Input should be an executive name like 'chief_technology_officer' or 'chief_marketing_officer'."
    )
    
    def __init__(self, registry_client: TeamRegistryClient):
        super().__init__()
        self.registry_client = registry_client
    
    def _run(self, executive_name: str) -> str:
        """Get teams for the specified executive."""
        try:
            teams = self.registry_client.get_executive_teams_sync(executive_name)
            
            if not teams:
                return f"No teams found reporting to '{executive_name}'"
            
            result = f"Teams reporting to {executive_name} ({len(teams)} total):\n\n"
            
            # Group by type
            teams_by_type = {}
            for team in teams:
                if team.type not in teams_by_type:
                    teams_by_type[team.type] = []
                teams_by_type[team.type].append(team)
            
            for team_type, type_teams in teams_by_type.items():
                result += f"{team_type.title()} Teams:\n"
                for team in type_teams:
                    result += f"  - {team.name}\n"
                    result += f"    Members: {len(team.members)}\n"
                    result += f"    Key Capabilities: {', '.join(list(team.capabilities)[:3])}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting executive teams: {e}")
            return f"Error retrieving executive teams: {str(e)}"


class UpdateTeamStatusTool(BaseTool):
    """Tool for updating team status in the registry."""
    
    name: str = "update_team_status"
    description: str = (
        "Update your team's status or capabilities in the registry. "
        "Use this to announce new capabilities or status changes. "
        "Input should be a JSON object with 'team_name', 'agent_name', and 'capabilities' array."
    )
    
    def __init__(self, registry_client: TeamRegistryClient):
        super().__init__()
        self.registry_client = registry_client
    
    def _run(self, update_json: str) -> str:
        """Update team status."""
        try:
            # Parse the JSON input
            try:
                update_data = json.loads(update_json)
                if not all(k in update_data for k in ['team_name', 'agent_name', 'capabilities']):
                    return "Input must include 'team_name', 'agent_name', and 'capabilities'"
            except json.JSONDecodeError:
                return "Invalid JSON. Please provide a valid JSON object."
            
            # Update capabilities
            success = self.registry_client.update_team_capabilities_sync(
                update_data['team_name'],
                update_data['agent_name'],
                update_data['capabilities']
            )
            
            if success:
                return (
                    f"Successfully updated {update_data['agent_name']}'s capabilities "
                    f"in team {update_data['team_name']}"
                )
            else:
                return "Failed to update team capabilities"
                
        except Exception as e:
            logger.error(f"Error updating team status: {e}")
            return f"Error updating status: {str(e)}"