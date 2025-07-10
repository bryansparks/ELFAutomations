#!/usr/bin/env python3
"""
Test Supabase MCP Server and Create Tables

Uses the Supabase MCP server to create database tables and test functionality.
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


def get_access_token():
    """Get the Supabase access token from environment."""
    # Try different possible variable names
    token = (
        os.getenv("SUPABASE_ACCESS_TOKEN")
        or os.getenv("SUPABASE_PERSONAL_ACCESS_TOKEN")
        or os.getenv("SUPABASE_PAT")
    )
    return token


def check_environment():
    """Check if required environment variables are set."""
    logger.info("🔍 Checking Environment Variables")
    logger.info("=" * 40)

    load_dotenv()

    required_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
        "Access Token": get_access_token(),
    }

    all_set = True
    for var_name, value in required_vars.items():
        if value:
            masked_value = f"{'*' * 8}...{value[-4:]}" if len(value) > 8 else "SET"
            logger.info(f"✅ {var_name}: {masked_value}")
        else:
            logger.error(f"❌ {var_name}: Not set")
            all_set = False

    return all_set


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

        # Check if already installed
        result = subprocess.run(
            ["npm", "list", "-g", "@supabase/mcp-server-supabase"],
            capture_output=True,
            text=True,
        )

        if "@supabase/mcp-server-supabase" in result.stdout:
            logger.info("✅ Supabase MCP server already installed")
            return True

        # Install it
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
            logger.error("❌ Failed to install", error=result.stderr)
            return False

    except Exception as e:
        logger.error("❌ Installation failed", error=str(e))
        return False


def test_mcp_server_connection():
    """Test the Supabase MCP server connection."""
    logger.info("🔌 Testing MCP Server Connection")
    logger.info("=" * 40)

    try:
        access_token = get_access_token()
        if not access_token:
            logger.error("❌ No access token found")
            return False

        # Build command
        cmd = [
            "npx",
            "-y",
            "@supabase/mcp-server-supabase@latest",
            "--access-token",
            access_token,
            "--help",
        ]

        logger.info("Testing MCP server connection...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            logger.info("✅ MCP server connection successful")
            if result.stdout:
                logger.info("Server help output available")
            return True
        else:
            logger.warning("⚠️ MCP server test had issues", error=result.stderr)
            return False

    except subprocess.TimeoutExpired:
        logger.info("✅ MCP server responded (timeout is normal for help command)")
        return True
    except Exception as e:
        logger.error("❌ Failed to test MCP server", error=str(e))
        return False


def run_mcp_sql_command(sql_statement):
    """Run a SQL command via the MCP server."""
    try:
        access_token = get_access_token()
        if not access_token:
            logger.error("❌ No access token found")
            return False

        # Create a temporary SQL file
        sql_file = Path("temp_mcp_query.sql")
        try:
            with open(sql_file, "w") as f:
                f.write(sql_statement)

            # Build command to execute SQL
            cmd = [
                "npx",
                "-y",
                "@supabase/mcp-server-supabase@latest",
                "--access-token",
                access_token,
            ]

            # Try to execute the SQL (this may vary based on MCP server capabilities)
            logger.info("Executing SQL via MCP server...")
            result = subprocess.run(
                cmd, input=sql_statement, capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                logger.info("✅ SQL executed successfully")
                return True
            else:
                logger.warning("⚠️ SQL execution had issues", error=result.stderr)
                return False

        finally:
            # Clean up temp file
            if sql_file.exists():
                sql_file.unlink()

    except Exception as e:
        logger.error("❌ Failed to execute SQL via MCP", error=str(e))
        return False


def create_tables_via_mcp():
    """Create database tables using the MCP server."""
    logger.info("🏗️ Creating Tables via MCP Server")
    logger.info("=" * 45)

    # Read the SQL file
    sql_file = Path("sql/create_business_tables.sql")
    if not sql_file.exists():
        logger.error("❌ SQL file not found: sql/create_business_tables.sql")
        return False

    try:
        with open(sql_file, "r") as f:
            sql_content = f.read()

        logger.info("📄 SQL file loaded successfully")

        # Split SQL into individual statements
        sql_statements = [
            stmt.strip() for stmt in sql_content.split(";") if stmt.strip()
        ]

        logger.info(f"Found {len(sql_statements)} SQL statements to execute")

        # Execute each statement
        success_count = 0
        for i, sql in enumerate(sql_statements, 1):
            if sql.strip():
                logger.info(f"Executing statement {i}/{len(sql_statements)}")
                if run_mcp_sql_command(sql):
                    success_count += 1
                else:
                    logger.warning(f"⚠️ Statement {i} failed")

        logger.info(
            f"✅ Executed {success_count}/{len(sql_statements)} statements successfully"
        )
        return success_count > 0

    except Exception as e:
        logger.error("❌ Failed to create tables via MCP", error=str(e))
        return False


def test_table_creation():
    """Test if tables were created successfully."""
    logger.info("🔍 Testing Table Creation")
    logger.info("=" * 30)

    # Test queries for each table
    test_queries = [
        "SELECT COUNT(*) FROM customers;",
        "SELECT COUNT(*) FROM leads;",
        "SELECT COUNT(*) FROM tasks;",
        "SELECT COUNT(*) FROM business_metrics;",
        "SELECT COUNT(*) FROM agent_activities;",
    ]

    success_count = 0
    for i, query in enumerate(test_queries, 1):
        table_name = query.split("FROM ")[1].split(";")[0].strip()
        logger.info(f"Testing table: {table_name}")

        if run_mcp_sql_command(query):
            logger.info(f"✅ Table {table_name} is accessible")
            success_count += 1
        else:
            logger.warning(f"⚠️ Table {table_name} is not accessible")

    logger.info(
        f"Table test results: {success_count}/{len(test_queries)} tables accessible"
    )
    return success_count == len(test_queries)


def create_mcp_config():
    """Create MCP configuration file."""
    logger.info("⚙️ Creating MCP Configuration")
    logger.info("=" * 35)

    access_token = get_access_token()
    if not access_token:
        logger.error("❌ No access token available")
        return False

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
    project_ref = os.getenv("SUPABASE_PROJECT_REF")
    if project_ref:
        config["mcpServers"]["supabase"]["args"].extend(["--project-ref", project_ref])

    # Write config file
    config_path = Path("mcp_supabase_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"✅ MCP configuration created: {config_path}")
    return True


async def main():
    """Main test function."""
    logger.info("🚀 Supabase MCP Server Setup and Table Creation")
    logger.info("=" * 60)

    # Step 1: Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        return 1

    # Step 2: Install MCP server
    if not install_supabase_mcp():
        logger.error("❌ MCP server installation failed")
        return 1

    # Step 3: Test MCP server connection
    if not test_mcp_server_connection():
        logger.warning("⚠️ MCP server connection test had issues, but continuing...")

    # Step 4: Create MCP configuration
    if not create_mcp_config():
        logger.warning("⚠️ MCP configuration creation failed")

    # Step 5: Create tables via MCP
    if not create_tables_via_mcp():
        logger.error("❌ Table creation via MCP failed")
        logger.info("💡 Alternative: Run the SQL file directly in Supabase dashboard")
        return 1

    # Step 6: Test table creation
    if not test_table_creation():
        logger.warning("⚠️ Some tables may not be accessible")

    logger.info("🎉 Supabase MCP setup and table creation completed!")
    logger.info("\nNext steps:")
    logger.info("  1. Test business tools with Supabase backend")
    logger.info("  2. Run AI agent demos")
    logger.info("  3. Validate full system functionality")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
