#!/usr/bin/env python3
"""Test script demonstrating registry-aware teams in action.

This script shows how teams can:
1. Discover each other by capability
2. Find teams for delegation
3. Understand organizational hierarchy
4. Collaborate on complex tasks
"""

import asyncio
import json
import os

# Add project root to path
import sys
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elf_automations.shared.mcp.client import MCPClient
from elf_automations.shared.registry import TeamRegistryClient
from elf_automations.shared.tools.registry_tools import (
    FindCollaboratorsTool,
    FindTeamByCapabilityTool,
    FindTeamByTypeTool,
    GetExecutiveTeamsTool,
    GetTeamHierarchyTool,
)
from elf_automations.shared.utils.logging import get_logger

logger = get_logger(__name__)


async def test_basic_registry_operations():
    """Test basic registry operations."""
    print("\n=== Testing Basic Registry Operations ===\n")

    # Initialize registry client
    mcp_client = MCPClient()
    registry_client = TeamRegistryClient(mcp_client)

    # Test 1: Register a team
    print("1. Registering a test team...")
    try:
        team = await registry_client.register_team(
            name="test-marketing-team",
            type="marketing",
            parent_name="executive-team",
            metadata={
                "created_by": "test_script",
                "purpose": "testing registry awareness",
            },
        )
        print(f"✓ Team registered: {team.name} (ID: {team.id})")
    except Exception as e:
        print(f"✗ Failed to register team: {e}")
        return

    # Test 2: Add team members
    print("\n2. Adding team members...")
    members = [
        (
            "marketing_manager",
            "Marketing Manager",
            ["marketing_strategy", "team_leadership", "campaign_planning"],
            True,
        ),
        (
            "content_writer",
            "Content Writer",
            ["content_creation", "copywriting", "blog_writing"],
            False,
        ),
        (
            "social_media_specialist",
            "Social Media Specialist",
            ["social_media", "content_creation", "analytics"],
            False,
        ),
    ]

    for name, role, capabilities, is_manager in members:
        success = await registry_client.add_team_member(
            team_name="test-marketing-team",
            agent_name=name,
            role=role,
            capabilities=capabilities,
            is_manager=is_manager,
        )
        if success:
            print(f"✓ Added {name} ({role})")
        else:
            print(f"✗ Failed to add {name}")

    # Test 3: Query team hierarchy
    print("\n3. Querying team hierarchy...")
    hierarchy = await registry_client.get_team_hierarchy("test-marketing-team")
    if hierarchy:
        print(f"✓ Team: {hierarchy.team.name}")
        print(f"  Type: {hierarchy.team.type}")
        print(f"  Members: {len(hierarchy.team.members)}")
        if hierarchy.parent:
            print(f"  Reports to: {hierarchy.parent.name}")
        print(f"  Children: {len(hierarchy.children)}")

    return registry_client


async def test_registry_tools():
    """Test the registry tools that agents would use."""
    print("\n=== Testing Registry Tools ===\n")

    # Initialize tools
    registry_client = TeamRegistryClient()

    # Test FindTeamByCapabilityTool
    print("1. Testing FindTeamByCapabilityTool...")
    capability_tool = FindTeamByCapabilityTool(registry_client)
    result = capability_tool._run("content_creation")
    print("Result:")
    print(result)
    print()

    # Test FindTeamByTypeTool
    print("2. Testing FindTeamByTypeTool...")
    type_tool = FindTeamByTypeTool(registry_client)
    result = type_tool._run("marketing")
    print("Result:")
    print(result)
    print()

    # Test GetTeamHierarchyTool
    print("3. Testing GetTeamHierarchyTool...")
    hierarchy_tool = GetTeamHierarchyTool(registry_client)
    result = hierarchy_tool._run("test-marketing-team")
    print("Result:")
    print(result)
    print()

    # Test FindCollaboratorsTool
    print("4. Testing FindCollaboratorsTool...")
    collaborator_tool = FindCollaboratorsTool(registry_client)
    capabilities_json = json.dumps(
        ["content_creation", "social_media", "marketing_strategy"]
    )
    result = collaborator_tool._run(capabilities_json)
    print("Result:")
    print(result)
    print()

    # Test GetExecutiveTeamsTool
    print("5. Testing GetExecutiveTeamsTool...")
    executive_tool = GetExecutiveTeamsTool(registry_client)
    result = executive_tool._run("chief_marketing_officer")
    print("Result:")
    print(result)


async def simulate_team_collaboration():
    """Simulate a scenario where teams need to collaborate."""
    print("\n=== Simulating Team Collaboration Scenario ===\n")

    registry_client = TeamRegistryClient()

    # Scenario: Product launch requiring multiple teams
    print("Scenario: Planning a product launch that requires:")
    print("- Product marketing")
    print("- Content creation")
    print("- Social media management")
    print("- Web development")
    print("- Data analytics")
    print()

    # Marketing manager uses FindCollaboratorsTool
    print("Marketing Manager is finding collaborators...")
    collaborator_tool = FindCollaboratorsTool(registry_client)

    required_capabilities = [
        "product_marketing",
        "content_creation",
        "social_media",
        "web_development",
        "data_analytics",
    ]

    result = collaborator_tool._run(json.dumps(required_capabilities))
    print(result)

    # Demonstrate delegation pattern
    print("\n--- Delegation Pattern ---")
    print("Marketing Manager delegates tasks based on capabilities:")

    # Find content team
    capability_tool = FindTeamByCapabilityTool(registry_client)
    content_teams = capability_tool._run("content_creation")
    print("\nContent Creation Task:")
    print(content_teams)

    # Find web dev team
    web_teams = capability_tool._run("web_development")
    print("\nWeb Development Task:")
    print(web_teams)


async def simulate_executive_oversight():
    """Simulate executive using registry for oversight."""
    print("\n=== Simulating Executive Oversight ===\n")

    registry_client = TeamRegistryClient()

    # CMO checking their teams
    print("Chief Marketing Officer reviewing organizational structure...")

    # Get all marketing teams
    executive_tool = GetExecutiveTeamsTool(registry_client)
    result = executive_tool._run("chief_marketing_officer")
    print(result)

    # Check specific team hierarchy
    print("\nDrilling down into specific team...")
    hierarchy_tool = GetTeamHierarchyTool(registry_client)
    result = hierarchy_tool._run("test-marketing-team")
    print(result)

    # Find all teams of a type
    print("\nFinding all marketing teams in organization...")
    type_tool = FindTeamByTypeTool(registry_client)
    result = type_tool._run("marketing")
    print(result)


async def main():
    """Run all test scenarios."""
    print("=" * 60)
    print("Registry Awareness Test Suite")
    print("=" * 60)

    try:
        # Test basic operations
        registry_client = await test_basic_registry_operations()

        # Test tools
        await test_registry_tools()

        # Test collaboration
        await simulate_team_collaboration()

        # Test executive oversight
        await simulate_executive_oversight()

        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n✗ Test suite failed: {e}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
