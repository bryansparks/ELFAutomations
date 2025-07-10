#!/usr/bin/env python3
"""
Test script for Team Registry MCP
"""

import asyncio
import json
import os

# Add parent directory to path
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.mcp import MCPClient


async def test_team_registry():
    """Test the team registry MCP operations"""

    print("🧪 Testing Team Registry MCP\n")

    # Initialize MCP client
    mcp_client = MCPClient(
        gateway_url=os.getenv("AGENTGATEWAY_URL", "http://localhost:8080")
    )

    try:
        # Test 1: Get team hierarchy
        print("1️⃣ Getting team hierarchy...")
        hierarchy = await mcp_client.call("team-registry", "get_team_hierarchy", {})
        print(f"✅ Found {len(hierarchy)} teams in hierarchy")

        # Test 2: Query executive team
        print("\n2️⃣ Querying executive team...")
        exec_teams = await mcp_client.call(
            "team-registry", "query_teams", {"department": "executive"}
        )
        print(f"✅ Found {len(exec_teams)} executive teams")

        # Test 3: Get teams managed by CTO
        print("\n3️⃣ Getting teams managed by CTO...")
        cto_teams = await mcp_client.call(
            "team-registry",
            "get_executive_teams",
            {"executive_role": "Chief Technology Officer"},
        )
        print(f"✅ CTO manages {len(cto_teams)} teams")
        for team in cto_teams:
            print(f"   - {team['team_name']} ({team['department']})")

        # Test 4: Get team composition
        print("\n4️⃣ Getting team composition summary...")
        composition = await mcp_client.call("team-registry", "get_team_composition", {})
        print(f"✅ Got composition for {len(composition)} teams")

        # Test 5: Query specific team
        print("\n5️⃣ Querying marketing team...")
        marketing = await mcp_client.call(
            "team-registry", "query_teams", {"team_name": "marketing-team"}
        )
        if marketing:
            team = marketing[0]
            print(f"✅ Marketing team:")
            print(f"   - Purpose: {team['purpose']}")
            print(f"   - Framework: {team['framework']}")
            print(f"   - LLM: {team['llm_provider']} / {team['llm_model']}")

            # Get team members
            members = await mcp_client.call(
                "team-registry", "get_team_members", {"team_name": "marketing-team"}
            )
            print(f"   - Members: {len(members)}")
            for member in members:
                print(
                    f"     • {member['role']} {'(Manager)' if member['is_manager'] else ''}"
                )

        print("\n✅ All tests passed! Team Registry MCP is working correctly.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. AgentGateway is running")
        print("2. Team Registry MCP is registered with AgentGateway")
        print("3. Supabase credentials are configured")
        print("4. Team registry schema is installed in Supabase")


if __name__ == "__main__":
    asyncio.run(test_team_registry())
