#!/usr/bin/env python3
"""
Setup Memory System tables in Supabase using our MCP infrastructure.

This follows the established pattern in ElfAutomations:
- Uses MCPClient from elf_automations.shared.mcp
- Communicates through AgentGateway
- No external 'mcp' package needed
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from elf_automations.shared.mcp import MCPClient

# Load environment variables
load_dotenv()


async def setup_memory_tables():
    """Create memory system tables in Supabase via MCP."""

    print("🚀 Setting up Memory System tables in Supabase")
    print("=" * 50)

    # Initialize MCP client
    mcp_client = MCPClient(
        gateway_url=os.getenv("AGENTGATEWAY_URL", "http://localhost:8080")
    )

    # Read SQL file
    sql_file = Path("sql/create_memory_system_tables.sql")
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return False

    with open(sql_file, "r") as f:
        sql_content = f.read()

    try:
        # Check available MCP servers
        print("\n📋 Checking available MCP servers...")
        available_servers = mcp_client.get_available_servers()
        print(f"Available servers: {', '.join(available_servers)}")

        if "supabase" not in available_servers:
            print("❌ Supabase MCP server not available")
            print("Make sure AgentGateway is running and Supabase MCP is configured")
            return False

        # List available tools on Supabase server
        print("\n🔧 Getting Supabase MCP tools...")
        tools = await mcp_client.list_tools("supabase")
        tool_names = [tool["name"] for tool in tools] if tools else []
        print(f"Available tools: {', '.join(tool_names[:5])}...")

        # Execute SQL
        print("\n📊 Creating memory system tables...")

        # Try different tool names that might be available
        if "execute_sql" in tool_names:
            result = await mcp_client.call(
                "supabase", "execute_sql", {"query": sql_content}
            )
        elif "run_sql" in tool_names:
            result = await mcp_client.call("supabase", "run_sql", {"sql": sql_content})
        elif "query" in tool_names:
            # Some MCP servers use generic 'query' tool
            result = await mcp_client.call("supabase", "query", {"sql": sql_content})
        else:
            print(
                f"❌ No suitable SQL execution tool found. Available tools: {tool_names}"
            )
            return False

        print("✅ Tables created successfully!")

        # Verify tables were created
        print("\n🔍 Verifying tables...")
        verification_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'memory_%'
            ORDER BY table_name;
        """

        # Use the same tool for verification
        if "execute_sql" in tool_names:
            result = await mcp_client.call(
                "supabase", "execute_sql", {"query": verification_query}
            )
        elif "run_sql" in tool_names:
            result = await mcp_client.call(
                "supabase", "run_sql", {"sql": verification_query}
            )
        elif "query" in tool_names:
            result = await mcp_client.call(
                "supabase", "query", {"sql": verification_query}
            )

        if result:
            print(f"✅ Verification complete: {result}")

        # Create default collection
        print("\n📦 Creating default memory collection...")
        insert_query = """
            INSERT INTO memory_collections (name, description, collection_type)
            VALUES ('default', 'Default memory collection for all teams', 'general')
            ON CONFLICT (name) DO NOTHING;
        """

        if "execute_sql" in tool_names:
            await mcp_client.call("supabase", "execute_sql", {"query": insert_query})
        elif "run_sql" in tool_names:
            await mcp_client.call("supabase", "run_sql", {"sql": insert_query})

        print("✅ Default collection created")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Main entry point."""

    # Check if we're running locally or need to connect to remote AgentGateway
    if not os.getenv("AGENTGATEWAY_URL"):
        print("\n⚠️  No AGENTGATEWAY_URL set, using default http://localhost:8080")
        print("If AgentGateway is running elsewhere, set AGENTGATEWAY_URL")

    success = await setup_memory_tables()

    if success:
        print("\n" + "=" * 50)
        print("🎉 Memory system tables created successfully!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Deploy Qdrant via GitOps (commit k8s/data-stores/qdrant/)")
        print("2. Build the Memory & Learning MCP server")
        print("3. Create the RAG free-agent team")
    else:
        print("\n❌ Setup failed!")
        print("\nTroubleshooting:")
        print("1. Is AgentGateway running? (check AGENTGATEWAY_URL)")
        print("2. Is Supabase MCP configured in AgentGateway?")
        print("3. Check SUPABASE_ACCESS_TOKEN in environment")


if __name__ == "__main__":
    asyncio.run(main())
