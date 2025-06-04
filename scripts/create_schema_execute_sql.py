#!/usr/bin/env python3
"""
Create Database Schema via Supabase MCP Server using execute_sql

Uses the Supabase MCP server's execute_sql tool to create the database schema.
"""

import asyncio
import json
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


async def get_project_info(session):
    """Get project information."""
    try:
        # List projects to get project ID
        logger.info("📋 Getting project information...")
        
        projects_result = await session.call_tool("list_projects")
        if projects_result.isError:
            logger.error("❌ Failed to list projects", error=projects_result.content)
            return None
        
        # Parse the projects result
        projects_data = projects_result.content
        logger.info("Projects found - extracting project ID...")
        
        # Try to extract project ID from the data
        if hasattr(projects_data, 'text'):
            projects_text = projects_data.text
        elif isinstance(projects_data, list) and len(projects_data) > 0:
            projects_text = str(projects_data[0])
        else:
            projects_text = str(projects_data)
        
        # Look for project ID in the response
        import re
        project_id_match = re.search(r'"id":\s*"([^"]+)"', projects_text)
        if project_id_match:
            project_id = project_id_match.group(1)
            logger.info(f"✅ Found project ID: {project_id}")
            return project_id
        
        logger.warning("⚠️ Could not extract project ID from projects list")
        return None
        
    except Exception as e:
        logger.error("❌ Failed to get project info", error=str(e))
        return None


async def execute_sql_statements(session, project_id, sql_statements):
    """Execute SQL statements one by one."""
    success_count = 0
    
    for i, sql in enumerate(sql_statements, 1):
        if not sql.strip():
            continue
            
        try:
            logger.info(f"Executing statement {i}/{len(sql_statements)}")
            
            result = await session.call_tool(
                "execute_sql",
                arguments={
                    "project_id": project_id,
                    "query": sql.strip()
                }
            )
            
            if result.isError:
                logger.warning(f"⚠️ Statement {i} failed: {result.content}")
            else:
                logger.info(f"✅ Statement {i} executed successfully")
                success_count += 1
                
        except Exception as e:
            logger.warning(f"⚠️ Statement {i} error: {str(e)}")
    
    return success_count


async def create_schema_via_mcp():
    """Create database schema using Supabase MCP server."""
    logger.info("🚀 Creating Schema via Supabase MCP Server (execute_sql)")
    logger.info("=" * 60)
    
    # Load environment
    load_dotenv()
    
    # Get access token
    access_token = (
        os.getenv("SUPABASE_ACCESS_TOKEN") or 
        os.getenv("SUPABASE_PERSONAL_ACCESS_TOKEN") or
        os.getenv("SUPABASE_PAT")
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
    
    # Split SQL into statements
    sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    logger.info(f"Found {len(sql_statements)} SQL statements to execute")
    
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
                
                # Get project information
                project_id = await get_project_info(session)
                if not project_id:
                    logger.error("❌ Could not get project ID")
                    return False
                
                # Check if execute_sql is available
                if "execute_sql" not in tool_names:
                    logger.error("❌ execute_sql tool not available")
                    return False
                
                logger.info("✅ execute_sql tool is available")
                
                # Execute SQL statements
                logger.info("🏗️ Executing SQL statements...")
                
                success_count = await execute_sql_statements(session, project_id, sql_statements)
                
                logger.info(f"✅ Executed {success_count}/{len(sql_statements)} statements successfully")
                
                # Test that tables were created by listing them
                logger.info("🔍 Verifying tables were created...")
                
                if "list_tables" in tool_names:
                    tables_result = await session.call_tool(
                        "list_tables",
                        arguments={"project_id": project_id}
                    )
                    if not tables_result.isError:
                        logger.info("📋 Database tables:")
                        logger.info(str(tables_result.content)[:1000])
                    else:
                        logger.warning("⚠️ Could not list tables", error=tables_result.content)
                
                return success_count > 0
                
    except Exception as e:
        logger.error("❌ Failed to create schema via MCP", error=str(e))
        return False


async def main():
    """Main function."""
    success = await create_schema_via_mcp()
    
    if success:
        logger.info("🎉 Database schema created successfully via MCP!")
        logger.info("\nNext steps:")
        logger.info("  1. Test business tools integration")
        logger.info("  2. Run AI agent demos")
        logger.info("  3. Validate full system functionality")
        return 0
    else:
        logger.error("❌ Schema creation failed")
        logger.info("💡 Alternative: Run the SQL manually in Supabase dashboard")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
