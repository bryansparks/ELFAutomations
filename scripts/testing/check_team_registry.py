#!/usr/bin/env python3
"""
Quick script to check if team registry tables exist in Supabase.
This is a temporary solution until we build the team-registry-mcp.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp_servers.base import ToolResponse
    from mcp_servers.supabase import SupabaseMCPServer

    print("🔍 Checking Team Registry status in Supabase...\n")

    # Initialize MCP server
    server = SupabaseMCPServer()

    # Check for teams table
    check_tables_sql = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('teams', 'team_members', 'team_relationships', 'team_audit_log')
    ORDER BY table_name;
    """

    print("Checking for team registry tables...")
    result = server.execute_sql(check_tables_sql)

    if isinstance(result, ToolResponse) and result.content:
        # Parse the result
        import json

        data = json.loads(result.content)

        if data and len(data) > 0:
            print("✅ Found existing team registry tables:")
            for row in data:
                print(f"   - {row['table_name']}")

            # Check if we have data
            count_sql = "SELECT COUNT(*) as count FROM teams;"
            count_result = server.execute_sql(count_sql)
            count_data = json.loads(count_result.content)
            team_count = count_data[0]["count"] if count_data else 0

            print(f"\n📊 Current teams in registry: {team_count}")

            if team_count > 0:
                # List existing teams
                list_sql = "SELECT name, framework, department, created_at FROM teams ORDER BY created_at;"
                list_result = server.execute_sql(list_sql)
                teams_data = json.loads(list_result.content)

                print("\n📋 Existing teams:")
                for team in teams_data:
                    print(
                        f"   - {team['name']} ({team['framework']}) in {team['department'] or 'root'}"
                    )

            print("\n✅ Team Registry is already set up and ready to use!")
            sys.exit(0)
        else:
            print("❌ Team registry tables not found.")
            print("📝 You need to run: python scripts/setup_team_registry.py")
            sys.exit(1)
    else:
        print("❌ Could not check table status")
        sys.exit(1)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you have the required dependencies installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error checking registry: {e}")
    sys.exit(1)
