#!/usr/bin/env python3
"""
Check if team registry tables exist in Supabase
"""

import asyncio
import os
import sys
from typing import Any, Dict, List

from dotenv import load_dotenv
from mcp.client.stdio import stdio_client

from mcp import ClientSession, StdioServerParameters

# Team registry tables we're looking for
TEAM_REGISTRY_TABLES = ["teams", "team_members", "team_relationships", "team_audit_log"]


async def check_team_registry_tables():
    """Check if team registry tables exist in Supabase."""
    print("🔍 Checking for Team Registry Tables in Supabase")
    print("=" * 50)

    # Load environment
    load_dotenv()

    # Get configuration
    access_token = (
        os.getenv("SUPABASE_ACCESS_TOKEN")
        or os.getenv("SUPABASE_PERSONAL_ACCESS_TOKEN")
        or os.getenv("SUPABASE_PAT")
    )

    project_id = os.getenv("SUPABASE_PROJECT_ID") or os.getenv("PROJECT_ID")

    if not access_token:
        print("❌ No access token found in environment")
        return False

    if not project_id:
        print("❌ No project ID found in environment")
        return False

    print(f"✅ Using project ID: {project_id}")

    # Set up MCP server parameters
    server_params = StdioServerParameters(
        command="npx",
        args=["@supabase/mcp-server-supabase@latest", "--access-token", access_token],
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("🔌 Connected to Supabase MCP server")

                # Initialize the session
                await session.initialize()
                print("✅ Session initialized")

                # Query for tables in public schema
                print("\n📊 Checking for team registry tables...")

                query = """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename IN ('teams', 'team_members', 'team_relationships', 'team_audit_log')
                ORDER BY tablename;
                """

                result = await session.call_tool(
                    "execute_sql", arguments={"project_id": project_id, "query": query}
                )

                if result.isError:
                    print(f"❌ Error executing query: {result.content}")
                    return False

                # Parse results
                content = result.content
                if isinstance(content, list) and len(content) > 0:
                    # Extract table data from result
                    result_text = str(content[0])

                    # Check which tables exist
                    existing_tables = []
                    for table in TEAM_REGISTRY_TABLES:
                        if table in result_text:
                            existing_tables.append(table)

                    print("\n📋 Team Registry Tables Status:")
                    for table in TEAM_REGISTRY_TABLES:
                        if table in existing_tables:
                            print(f"  ✅ {table} - EXISTS")
                        else:
                            print(f"  ❌ {table} - NOT FOUND")

                    if len(existing_tables) == len(TEAM_REGISTRY_TABLES):
                        print("\n✅ All team registry tables exist!")

                        # Get row counts
                        print("\n📊 Getting row counts...")
                        for table in existing_tables:
                            count_query = f"SELECT COUNT(*) as count FROM {table};"
                            count_result = await session.call_tool(
                                "execute_sql",
                                arguments={
                                    "project_id": project_id,
                                    "query": count_query,
                                },
                            )
                            if not count_result.isError:
                                print(f"  - {table}: {count_result.content[0]}")

                        return True
                    else:
                        print(
                            f"\n⚠️  Only {len(existing_tables)}/{len(TEAM_REGISTRY_TABLES)} tables exist"
                        )
                        return False
                else:
                    print("❌ No team registry tables found")
                    return False

    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {str(e)}")
        return False


async def main():
    """Main function."""
    success = await check_team_registry_tables()

    if success:
        print("\n🎉 Team registry tables are already set up!")
    else:
        print("\n⚠️  Team registry tables need to be created")
        print("Run: python scripts/setup_team_registry.py")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
