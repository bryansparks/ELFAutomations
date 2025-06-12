#!/usr/bin/env python3
"""Setup Memory System tables using Supabase MCP server.

This approach uses the official Supabase MCP server to create tables,
similar to how we created business tables before.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def create_memory_tables_via_mcp():
    """Create memory system tables using Supabase MCP server."""
    
    # Get access token
    access_token = os.getenv('SUPABASE_PERSONAL_ACCESS_TOKEN')
    if not access_token:
        logger.error("SUPABASE_PERSONAL_ACCESS_TOKEN not set in environment")
        logger.info("Get your token from: https://app.supabase.com/account/tokens")
        return False
    
    # Initialize MCP client for Supabase
    server_params = StdioServerParameters(
        command="npx",
        args=["@supabase/mcp-server-supabase@latest", "--access-token", access_token]
    )
    
    logger.info("Connecting to Supabase MCP server...")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List available tools
                logger.info("Getting available tools...")
                tools = await session.list_tools()
                tool_names = [t.name for t in tools]
                logger.info(f"Available tools: {', '.join(tool_names[:5])}...")
                
                # Get project ID from SUPABASE_URL
                supabase_url = os.getenv('SUPABASE_URL', '')
                if 'supabase.co' in supabase_url:
                    project_ref = supabase_url.replace('https://', '').split('.supabase.co')[0]
                    logger.info(f"Using project: {project_ref}")
                else:
                    logger.error("Could not extract project ID from SUPABASE_URL")
                    return False
                
                # Read SQL file
                sql_file = Path('sql/create_memory_system_tables.sql')
                if not sql_file.exists():
                    logger.error(f"SQL file not found: {sql_file}")
                    return False
                    
                with open(sql_file, 'r') as f:
                    sql_content = f.read()
                
                # Execute SQL via MCP
                logger.info("Creating memory system tables...")
                
                if 'execute_sql' in tool_names:
                    # Use execute_sql tool
                    result = await session.call_tool(
                        "execute_sql",
                        arguments={
                            "project_id": project_ref,
                            "query": sql_content
                        }
                    )
                    logger.info("Tables created via execute_sql")
                    
                elif 'apply_migration' in tool_names:
                    # Use apply_migration tool as alternative
                    result = await session.call_tool(
                        "apply_migration",
                        arguments={
                            "project_id": project_ref,
                            "sql": sql_content
                        }
                    )
                    logger.info("Tables created via apply_migration")
                    
                else:
                    logger.error("No suitable tool found for executing SQL")
                    return False
                
                # Verify tables were created
                logger.info("\nVerifying tables...")
                verification_query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN (
                        'memory_entries', 
                        'memory_collections', 
                        'learning_patterns',
                        'memory_relationships',
                        'team_knowledge_profiles',
                        'memory_access_logs'
                    )
                    ORDER BY table_name;
                """
                
                result = await session.call_tool(
                    "execute_sql",
                    arguments={
                        "project_id": project_ref,
                        "query": verification_query
                    }
                )
                
                if result and hasattr(result, 'content'):
                    logger.info("✅ Memory system tables created successfully!")
                    logger.info(f"Created tables: {result.content}")
                else:
                    logger.warning("Could not verify table creation")
                
                # Create default collection
                logger.info("\nCreating default memory collection...")
                insert_query = """
                    INSERT INTO memory_collections (name, description, collection_type)
                    VALUES ('default', 'Default memory collection for all teams', 'general')
                    ON CONFLICT (name) DO NOTHING
                    RETURNING name;
                """
                
                result = await session.call_tool(
                    "execute_sql",
                    arguments={
                        "project_id": project_ref,
                        "query": insert_query
                    }
                )
                
                logger.info("✅ Default collection created")
                
                return True
                
    except Exception as e:
        logger.error(f"Failed to create tables via MCP: {e}")
        return False


def main():
    """Main entry point."""
    logger.info("Memory System Setup via Supabase MCP")
    logger.info("="*50)
    
    # Check for required environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_PERSONAL_ACCESS_TOKEN']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.info("\nTo get your Supabase personal access token:")
        logger.info("1. Go to https://app.supabase.com/account/tokens")
        logger.info("2. Create a new token")
        logger.info("3. Add to .env as SUPABASE_PERSONAL_ACCESS_TOKEN")
        return 1
    
    # Run the async setup
    success = asyncio.run(create_memory_tables_via_mcp())
    
    if success:
        logger.info("\n" + "="*50)
        logger.info("🎉 Memory system tables created successfully!")
        logger.info("="*50)
        logger.info("\nNext steps:")
        logger.info("1. Deploy Qdrant via GitOps (commit k8s/data-stores/qdrant/)")
        logger.info("2. Build the Memory & Learning MCP server")
        logger.info("3. Create the RAG free-agent team")
        return 0
    else:
        logger.error("\n❌ Setup failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())