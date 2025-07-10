"""
Shared tools for ElfAutomations agents.

This module provides reusable tools that can be used by any agent,
including registry tools for team discovery and collaboration.
"""

from .registry_tools import (
    FindCollaboratorsTool,
    FindTeamByCapabilityTool,
    FindTeamByTypeTool,
    GetExecutiveTeamsTool,
    GetTeamHierarchyTool,
    UpdateTeamStatusTool,
    get_registry_tools_for_agent,
    get_registry_tools_for_executive,
)

__all__ = [
    # Registry tools
    "FindTeamByCapabilityTool",
    "FindTeamByTypeTool",
    "GetTeamHierarchyTool",
    "FindCollaboratorsTool",
    "GetExecutiveTeamsTool",
    "UpdateTeamStatusTool",
    # Helper functions
    "get_registry_tools_for_agent",
    "get_registry_tools_for_executive",
]
