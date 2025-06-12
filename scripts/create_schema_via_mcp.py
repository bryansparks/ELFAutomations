#!/usr/bin/env python3
"""
Create Database Schema via Supabase MCP Server

Uses the Supabase MCP server's apply_migration tool to create the database schema.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv
from mcp.client.stdio import stdio_client

from mcp import ClientSession, StdioServerParameters

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def create_schema_via_mcp():
    """Create database schema using Supabase MCP server."""
    logger.info("🚀 Creating Schema via Supabase MCP Server")
    logger.info("=" * 50)

    # Load environment
    load_dotenv()

    # Get access token
    access_token = (
        os.getenv("SUPABASE_ACCESS_TOKEN")
        or os.getenv("SUPABASE_PERSONAL_ACCESS_TOKEN")
        or os.getenv("SUPABASE_PAT")
    )

    if not access_token:
        logger.error("❌ No access token found")
        return False

    logger.info("✅ Access token found")

    # Read SQL file
    sql_file = Path("sql/create_business_tables.sql")
    if not sql_file.exists():
        logger.error(f"❌ SQL file not found: {sql_file}")
        return False

    with open(sql_file, "r") as f:
        sql_content = f.read()

    logger.info(f"📄 SQL file loaded ({len(sql_content)} characters)")

    # Set up MCP server parameters
    server_params = StdioServerParameters(
        command="npx",
        args=["@supabase/mcp-server-supabase@latest", "--access-token", access_token],
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                logger.info("🔌 Connected to Supabase MCP server")

                # Initialize the session
                await session.initialize()

                # List available tools
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                logger.info(f"📋 Available tools: {', '.join(tool_names)}")

                # Check if apply_migration is available
                if "apply_migration" not in tool_names:
                    logger.error("❌ apply_migration tool not available")
                    return False

                logger.info("✅ apply_migration tool is available")

                # Apply the migration
                logger.info("🏗️ Applying database migration...")

                result = await session.call_tool(
                    "apply_migration",
                    arguments={"sql": sql_content, "name": "create_business_tables"},
                )

                if result.isError:
                    logger.error("❌ Migration failed", error=result.content)
                    return False

                logger.info("✅ Migration applied successfully!")
                logger.info("Migration result:", result=result.content)

                # Test that tables were created by listing them
                logger.info("🔍 Verifying tables were created...")

                if "list_tables" in tool_names:
                    tables_result = await session.call_tool("list_tables")
                    if not tables_result.isError:
                        logger.info("📋 Database tables:", tables=tables_result.content)
                    else:
                        logger.warning(
                            "⚠️ Could not list tables", error=tables_result.content
                        )

                return True

    except Exception as e:
        logger.error("❌ Failed to create schema via MCP", error=str(e))
        return False


async def main():
    """Main function."""
    success = await create_schema_via_mcp()

    if success:
        logger.info("🎉 Database schema created successfully!")
        logger.info("\nNext steps:")
        logger.info("  1. Test business tools integration")
        logger.info("  2. Run AI agent demos")
        logger.info("  3. Validate full system functionality")
        return 0
    else:
        logger.error("❌ Schema creation failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
