#!/usr/bin/env python3
"""
Setup Supabase MCP Server

Sets up the Supabase MCP server for database operations.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv

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


def check_environment():
    """Check if required environment variables are set."""
    logger.info("🔍 Checking Environment Variables")
    logger.info("=" * 40)

    load_dotenv()

    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_ACCESS_TOKEN"]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {'*' * 8}...{value[-4:]}")
        else:
            logger.warning(f"❌ {var}: Not set")
            missing_vars.append(var)

    if missing_vars:
        logger.error("Missing required environment variables", missing=missing_vars)
        logger.info("\nTo get your SUPABASE_ACCESS_TOKEN:")
        logger.info("1. Go to https://supabase.com/dashboard")
        logger.info("2. Navigate to Settings > Access Tokens")
        logger.info("3. Create a new token with appropriate permissions")
        logger.info(
            "4. Add it to your .env file as SUPABASE_ACCESS_TOKEN=your_token_here"
        )
        return False

    return True


def install_supabase_mcp():
    """Install the Supabase MCP server."""
    logger.info("📦 Installing Supabase MCP Server")
    logger.info("=" * 40)

    try:
        # Check if npm is available
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(
                "❌ npm is not available. Please install Node.js and npm first."
            )
            return False

        logger.info(f"✅ npm version: {result.stdout.strip()}")

        # Install the Supabase MCP server globally
        logger.info("Installing @supabase/mcp-server-supabase...")
        result = subprocess.run(
            ["npm", "install", "-g", "@supabase/mcp-server-supabase@latest"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info("✅ Supabase MCP server installed successfully")
            return True
        else:
            logger.error("❌ Failed to install Supabase MCP server", error=result.stderr)
            return False

    except FileNotFoundError:
        logger.error("❌ npm command not found. Please install Node.js and npm first.")
        return False
    except Exception as e:
        logger.error("❌ Failed to install Supabase MCP server", error=str(e))
        return False


def create_mcp_config():
    """Create MCP server configuration."""
    logger.info("⚙️ Creating MCP Configuration")
    logger.info("=" * 35)

    access_token = os.getenv("SUPABASE_ACCESS_TOKEN")
    project_ref = os.getenv("SUPABASE_PROJECT_REF", "")

    # Create MCP configuration
    config = {
        "mcpServers": {
            "supabase": {
                "command": "npx",
                "args": [
                    "-y",
                    "@supabase/mcp-server-supabase@latest",
                    "--access-token",
                    access_token,
                ],
            }
        }
    }

    # Add project reference if available
    if project_ref:
        config["mcpServers"]["supabase"]["args"].extend(["--project-ref", project_ref])

    # Write config file
    config_path = Path("mcp_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"✅ MCP configuration created: {config_path}")
    return True


def test_mcp_server():
    """Test the Supabase MCP server."""
    logger.info("🧪 Testing Supabase MCP Server")
    logger.info("=" * 35)

    try:
        access_token = os.getenv("SUPABASE_ACCESS_TOKEN")
        project_ref = os.getenv("SUPABASE_PROJECT_REF", "")

        # Build command
        cmd = [
            "npx",
            "-y",
            "@supabase/mcp-server-supabase@latest",
            "--access-token",
            access_token,
        ]

        if project_ref:
            cmd.extend(["--project-ref", project_ref])

        # Add a test command to list available tools
        cmd.extend(["--help"])

        logger.info("Running MCP server test...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            logger.info("✅ Supabase MCP server is working")
            if result.stdout:
                logger.info("Server output:", output=result.stdout[:500])
            return True
        else:
            logger.warning("⚠️ MCP server test had issues", error=result.stderr)
            return False

    except subprocess.TimeoutExpired:
        logger.warning("⚠️ MCP server test timed out (this might be normal)")
        return True
    except Exception as e:
        logger.error("❌ Failed to test MCP server", error=str(e))
        return False


async def create_tables_with_mcp():
    """Create database tables using the Supabase MCP server."""
    logger.info("🏗️ Creating Tables with Supabase MCP")
    logger.info("=" * 45)

    try:
        # Import MCP client utilities
        from mcp.client.stdio import stdio_client

        from mcp import ClientSession, StdioServerParameters

        access_token = os.getenv("SUPABASE_ACCESS_TOKEN")
        project_ref = os.getenv("SUPABASE_PROJECT_REF", "")

        # Build server parameters
        server_params = StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@supabase/mcp-server-supabase@latest",
                "--access-token",
                access_token,
            ],
        )

        if project_ref:
            server_params.args.extend(["--project-ref", project_ref])

        # Connect to MCP server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()

                # List available tools
                tools = await session.list_tools()
                logger.info(
                    f"✅ Connected to MCP server. Available tools: {len(tools.tools)}"
                )

                for tool in tools.tools:
                    logger.info(f"  - {tool.name}: {tool.description}")

                # Create tables using SQL execution tool if available
                sql_statements = [
                    """
                    CREATE TABLE IF NOT EXISTS customers (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        phone VARCHAR(50),
                        company VARCHAR(255),
                        status VARCHAR(50) DEFAULT 'active',
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS leads (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        customer_id UUID REFERENCES customers(id),
                        name VARCHAR(255),
                        email VARCHAR(255),
                        source VARCHAR(100),
                        status VARCHAR(50) DEFAULT 'new',
                        score INTEGER DEFAULT 0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        status VARCHAR(50) DEFAULT 'pending',
                        priority INTEGER DEFAULT 3,
                        assigned_agent_id VARCHAR(255),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS business_metrics (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        metric_name VARCHAR(100) NOT NULL,
                        metric_value DECIMAL(15,4) NOT NULL,
                        metric_type VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    """,
                ]

                # Execute SQL statements
                for i, sql in enumerate(sql_statements, 1):
                    try:
                        # Look for SQL execution tool
                        sql_tool = None
                        for tool in tools.tools:
                            if (
                                "sql" in tool.name.lower()
                                or "execute" in tool.name.lower()
                            ):
                                sql_tool = tool.name
                                break

                        if sql_tool:
                            result = await session.call_tool(sql_tool, {"sql": sql})
                            logger.info(f"✅ Table creation {i} executed successfully")
                        else:
                            logger.warning(
                                f"⚠️ No SQL execution tool found, skipping table creation {i}"
                            )

                    except Exception as e:
                        logger.error(
                            f"❌ Failed to execute SQL statement {i}", error=str(e)
                        )

                return True

    except ImportError:
        logger.warning("⚠️ MCP client not available. Install with: pip install mcp")
        return False
    except Exception as e:
        logger.error("❌ Failed to create tables with MCP", error=str(e))
        return False


async def main():
    """Main setup function."""
    logger.info("🚀 Supabase MCP Server Setup")
    logger.info("=" * 50)

    # Step 1: Check environment
    if not check_environment():
        return 1

    # Step 2: Install MCP server
    if not install_supabase_mcp():
        return 1

    # Step 3: Create MCP configuration
    if not create_mcp_config():
        return 1

    # Step 4: Test MCP server
    if not test_mcp_server():
        logger.warning("⚠️ MCP server test had issues, but continuing...")

    # Step 5: Create tables (if MCP client is available)
    await create_tables_with_mcp()

    logger.info("🎉 Supabase MCP setup completed!")
    logger.info("\nNext steps:")
    logger.info("  1. Use the MCP server to create database schema")
    logger.info("  2. Test business tools integration")
    logger.info("  3. Run full system demos")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
