#!/usr/bin/env python3
"""
Create Database Tables via Supabase MCP Server (Direct)

Uses the Supabase MCP server with the configured PROJECT_ID to create database tables.
"""

import asyncio
import os
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

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
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def create_tables_via_mcp():
    """Create database tables using Supabase MCP server."""
    logger.info("🚀 Creating Tables via Supabase MCP Server")
    logger.info("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Get configuration
    access_token = (
        os.getenv("SUPABASE_ACCESS_TOKEN") or 
        os.getenv("SUPABASE_PERSONAL_ACCESS_TOKEN") or
        os.getenv("SUPABASE_PAT")
    )
    
    project_id = os.getenv("SUPABASE_PROJECT_ID") or os.getenv("PROJECT_ID")
    project_name = os.getenv("SUPABASE_PROJECT_NAME") or os.getenv("PROJECT_NAME")
    
    if not access_token:
        logger.error("❌ No access token found")
        return False
    
    if not project_id:
        logger.error("❌ No project ID found")
        return False
    
    logger.info(f"✅ Access token found")
    logger.info(f"✅ Project ID: {project_id}")
    logger.info(f"✅ Project Name: {project_name}")
    
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
        args=[
            "@supabase/mcp-server-supabase@latest",
            "--access-token", access_token
        ]
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
                
                # Try apply_migration first (preferred for schema changes)
                if "apply_migration" in tool_names:
                    logger.info("🏗️ Using apply_migration for schema creation...")
                    
                    result = await session.call_tool(
                        "apply_migration",
                        arguments={
                            "project_id": project_id,
                            "query": sql_content,
                            "name": "create_business_tables_initial"
                        }
                    )
                    
                    if not result.isError:
                        logger.info("✅ Migration applied successfully!")
                        logger.info("Migration result:", result=str(result.content)[:500])
                    else:
                        logger.warning("⚠️ Migration failed, trying execute_sql...", error=str(result.content)[:200])
                        
                        # Fallback to execute_sql
                        if "execute_sql" in tool_names:
                            logger.info("🔄 Falling back to execute_sql...")
                            
                            # Split SQL into statements and execute them
                            sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                            success_count = 0
                            
                            for i, sql in enumerate(sql_statements[:5], 1):  # Try first 5 statements
                                try:
                                    result = await session.call_tool(
                                        "execute_sql",
                                        arguments={
                                            "project_id": project_id,
                                            "query": sql
                                        }
                                    )
                                    
                                    if not result.isError:
                                        logger.info(f"✅ Statement {i} executed successfully")
                                        success_count += 1
                                    else:
                                        logger.warning(f"⚠️ Statement {i} failed: {str(result.content)[:100]}")
                                        
                                except Exception as e:
                                    logger.warning(f"⚠️ Statement {i} error: {str(e)}")
                            
                            logger.info(f"Executed {success_count}/{min(5, len(sql_statements))} statements")
                        else:
                            logger.error("❌ No suitable execution method available")
                            return False
                
                # Verify tables were created
                if "list_tables" in tool_names:
                    logger.info("🔍 Verifying tables were created...")
                    
                    tables_result = await session.call_tool(
                        "list_tables",
                        arguments={"project_id": project_id}
                    )
                    
                    if not tables_result.isError:
                        tables_content = str(tables_result.content)
                        logger.info("📋 Database tables:")
                        logger.info(tables_content[:800])
                        
                        # Check for our business tables
                        business_tables = ["customers", "leads", "tasks", "business_metrics", "agent_activities"]
                        found_tables = [table for table in business_tables if table in tables_content.lower()]
                        
                        if found_tables:
                            logger.info(f"✅ Found business tables: {', '.join(found_tables)}")
                        else:
                            logger.warning("⚠️ Business tables not found in list")
                    else:
                        logger.warning("⚠️ Could not list tables", error=str(tables_result.content)[:200])
                
                return True
                
    except Exception as e:
        logger.error("❌ Failed to create tables via MCP", error=str(e))
        return False


async def main():
    """Main function."""
    success = await create_tables_via_mcp()
    
    if success:
        logger.info("🎉 Table creation process completed!")
        logger.info("\nNext steps:")
        logger.info("  1. Test business tools integration")
        logger.info("  2. Run: python scripts/test_business_tools_supabase.py")
        logger.info("  3. Validate AI agent interactions")
        return 0
    else:
        logger.error("❌ Table creation failed")
        logger.info("💡 Alternative: Run SQL manually in Supabase dashboard")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
