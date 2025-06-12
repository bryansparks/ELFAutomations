#!/usr/bin/env python3
"""
Test Supabase MCP Server Connection

Simple test to verify MCP server connectivity and available tools.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from mcp.client.stdio import stdio_client

from mcp import ClientSession, StdioServerParameters


async def test_mcp_connection():
    """Test MCP server connection."""
    print("🚀 Testing Supabase MCP Server Connection")
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
        print("❌ No access token found")
        return False

    if not project_id:
        print("❌ No project ID found")
        return False

    print(f"✅ Access token: {'*' * 8}...{access_token[-4:]}")
    print(f"✅ Project ID: {project_id}")

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

                # List available tools
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                print(f"📋 Available tools ({len(tool_names)}):")
                for tool in tool_names:
                    print(f"  - {tool}")

                # Test list_tables
                if "list_tables" in tool_names:
                    print("\n🔍 Testing list_tables...")

                    tables_result = await session.call_tool(
                        "list_tables", arguments={"project_id": project_id}
                    )

                    if not tables_result.isError:
                        print("✅ list_tables successful:")
                        print(str(tables_result.content)[:500])
                    else:
                        print("❌ list_tables failed:")
                        print(str(tables_result.content)[:300])

                # Test a simple SQL query
                if "execute_sql" in tool_names:
                    print("\n🔍 Testing execute_sql with simple query...")

                    sql_result = await session.call_tool(
                        "execute_sql",
                        arguments={
                            "project_id": project_id,
                            "query": "SELECT 1 as test_value;",
                        },
                    )

                    if not sql_result.isError:
                        print("✅ execute_sql successful:")
                        print(str(sql_result.content)[:300])
                    else:
                        print("❌ execute_sql failed:")
                        print(str(sql_result.content)[:300])

                return True

    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {str(e)}")
        return False


async def main():
    """Main function."""
    success = await test_mcp_connection()

    if success:
        print("\n🎉 MCP server connection test completed!")
    else:
        print("\n❌ MCP server connection test failed")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
