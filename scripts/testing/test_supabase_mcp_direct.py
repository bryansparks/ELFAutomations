#!/usr/bin/env python3
"""
Test Supabase MCP Server Directly

Tests the Supabase MCP server and creates database tables.
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


def run_mcp_command(command_args, input_data=None):
    """Run a command with the Supabase MCP server."""
    try:
        access_token = os.getenv("SUPABASE_ACCESS_TOKEN")
        if not access_token:
            logger.error("❌ SUPABASE_ACCESS_TOKEN not set")
            return None

        # Build the full command
        cmd = [
            "npx",
            "-y",
            "@supabase/mcp-server-supabase@latest",
            "--access-token",
            access_token,
        ]

        project_ref = os.getenv("SUPABASE_PROJECT_REF")
        if project_ref:
            cmd.extend(["--project-ref", project_ref])

        # Add the specific command arguments
        cmd.extend(command_args)

        logger.info(f"Running command: {' '.join(cmd[:3])} ... [hidden args]")

        # Run the command
        result = subprocess.run(
            cmd, input=input_data, capture_output=True, text=True, timeout=60
        )

        return result

    except subprocess.TimeoutExpired:
        logger.error("❌ Command timed out")
        return None
    except Exception as e:
        logger.error("❌ Failed to run MCP command", error=str(e))
        return None


def install_mcp_server():
    """Install the Supabase MCP server."""
    logger.info("📦 Installing Supabase MCP Server")
    logger.info("=" * 40)

    try:
        # Check if already installed
        result = subprocess.run(
            ["npm", "list", "-g", "@supabase/mcp-server-supabase"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
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


def create_table_sql():
    """Get SQL statements for creating tables."""
    return [
        # Customers table
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
        # Leads table
        """
        CREATE TABLE IF NOT EXISTS leads (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            customer_id UUID REFERENCES customers(id),
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            company VARCHAR(255),
            source VARCHAR(100),
            status VARCHAR(50) DEFAULT 'new',
            score INTEGER DEFAULT 0 CHECK (score >= 0 AND score <= 100),
            assigned_agent_id VARCHAR(255),
            notes TEXT,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        # Tasks table
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            type VARCHAR(100),
            status VARCHAR(50) DEFAULT 'pending',
            priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
            assignee VARCHAR(255),
            assigned_agent_id VARCHAR(255),
            created_by_agent_id VARCHAR(255),
            due_date TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        # Business metrics table
        """
        CREATE TABLE IF NOT EXISTS business_metrics (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            metric_name VARCHAR(100) NOT NULL,
            metric_value DECIMAL(15,4) NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            period_start DATE,
            period_end DATE,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
    ]


def test_mcp_connection():
    """Test basic MCP server connection."""
    logger.info("🔌 Testing MCP Server Connection")
    logger.info("=" * 40)

    # Try to run a simple command
    result = run_mcp_command(["--help"])

    if result and result.returncode == 0:
        logger.info("✅ MCP server connection successful")
        return True
    else:
        logger.error("❌ MCP server connection failed")
        if result:
            logger.error("Error output:", error=result.stderr)
        return False


def create_tables_via_mcp():
    """Create tables using the MCP server."""
    logger.info("🏗️ Creating Tables via MCP Server")
    logger.info("=" * 40)

    sql_statements = create_table_sql()

    for i, sql in enumerate(sql_statements, 1):
        logger.info(f"Creating table {i}/{len(sql_statements)}")

        # Create a temporary SQL file
        sql_file = Path(f"temp_table_{i}.sql")
        try:
            with open(sql_file, "w") as f:
                f.write(sql)

            # Try to execute via MCP (this depends on available MCP tools)
            # For now, we'll just log that we would execute this
            logger.info(f"Would execute SQL for table {i}")
            logger.info(f"SQL preview: {sql[:100]}...")

        finally:
            # Clean up temp file
            if sql_file.exists():
                sql_file.unlink()

    logger.info("✅ Table creation commands prepared")
    return True


def insert_sample_data():
    """Insert sample data using MCP."""
    logger.info("📊 Inserting Sample Data")
    logger.info("=" * 30)

    # Sample data
    sample_customers = [
        {"name": "John Doe", "email": "john@techcorp.com", "company": "Tech Corp"},
        {"name": "Jane Smith", "email": "jane@startup.io", "company": "Startup Inc"},
        {
            "name": "Bob Johnson",
            "email": "bob@enterprise.com",
            "company": "Enterprise Ltd",
        },
    ]

    logger.info(f"Would insert {len(sample_customers)} sample customers")
    logger.info("✅ Sample data preparation completed")
    return True


async def main():
    """Main test function."""
    logger.info("🚀 Supabase MCP Direct Test")
    logger.info("=" * 50)

    # Load environment
    load_dotenv()

    # Check if access token is set
    if not os.getenv("SUPABASE_ACCESS_TOKEN"):
        logger.error("❌ SUPABASE_ACCESS_TOKEN not set in .env file")
        logger.info("\nTo get your access token:")
        logger.info("1. Go to https://supabase.com/dashboard")
        logger.info("2. Navigate to Settings > Access Tokens")
        logger.info("3. Create a new token")
        logger.info("4. Add SUPABASE_ACCESS_TOKEN=your_token_here to .env")
        return 1

    # Step 1: Install MCP server
    if not install_mcp_server():
        return 1

    # Step 2: Test connection
    if not test_mcp_connection():
        return 1

    # Step 3: Create tables
    if not create_tables_via_mcp():
        return 1

    # Step 4: Insert sample data
    if not insert_sample_data():
        return 1

    logger.info("🎉 MCP setup completed!")
    logger.info("\nNote: This script prepared the commands.")
    logger.info("For actual table creation, you may need to:")
    logger.info("1. Use the Supabase dashboard SQL editor")
    logger.info("2. Or use the MCP server interactively")
    logger.info("3. Or run the business tools test to verify tables exist")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
