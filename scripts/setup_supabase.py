#!/usr/bin/env python3
"""
Supabase Integration Setup

Configures the ELF Automations platform to use Supabase as the primary database
and integrates the Supabase MCP server for enhanced AI-database interactions.
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


def check_node_npm():
    """Check if Node.js and npm are available."""
    try:
        node_result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, timeout=5
        )
        npm_result = subprocess.run(
            ["npm", "--version"], capture_output=True, text=True, timeout=5
        )

        if node_result.returncode == 0 and npm_result.returncode == 0:
            logger.info(
                "Node.js and npm available",
                node_version=node_result.stdout.strip(),
                npm_version=npm_result.stdout.strip(),
            )
            return True
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def install_supabase_mcp():
    """Install the Supabase MCP server globally."""
    try:
        logger.info("Installing Supabase MCP server...")
        result = subprocess.run(
            ["npm", "install", "-g", "@supabase/mcp-server-supabase"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            logger.info("Supabase MCP server installed successfully")
            return True
        else:
            logger.error("Failed to install Supabase MCP server", error=result.stderr)
            return False
    except Exception as e:
        logger.error("Error installing Supabase MCP server", error=str(e))
        return False


def create_mcp_config():
    """Create MCP configuration for Supabase integration."""
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"
    config_dir.mkdir(exist_ok=True)

    # Load environment variables to get Supabase settings
    load_dotenv()

    # Get access token with multiple possible names
    supabase_access_token = (
        os.getenv("SUPABASE_ACCESS_TOKEN")
        or os.getenv("SUPABASE_PERSONAL_ACCESS_TOKEN")
        or os.getenv("SUPABASE_PAT")
    )

    supabase_project_ref = os.getenv("SUPABASE_PROJECT_REF")

    if not supabase_access_token:
        logger.error(
            "SUPABASE_ACCESS_TOKEN (or SUPABASE_PERSONAL_ACCESS_TOKEN): Not set"
        )
        return False

    # Create MCP configuration
    mcp_config = {
        "mcpServers": {
            "supabase": {
                "command": "npx",
                "args": [
                    "-y",
                    "@supabase/mcp-server-supabase@latest",
                    "--access-token",
                    supabase_access_token,
                ],
            },
            "supabase-postgrest": {
                "command": "npx",
                "args": ["-y", "@supabase/mcp-server-postgrest@latest"],
                "env": {
                    "SUPABASE_URL": os.getenv("SUPABASE_URL", ""),
                    "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY", ""),
                },
            },
        }
    }

    # Add project scoping if available
    if supabase_project_ref:
        mcp_config["mcpServers"]["supabase"]["args"].extend(
            ["--project-ref", supabase_project_ref]
        )

    # Save configuration
    config_file = config_dir / "mcp_config.json"
    with open(config_file, "w") as f:
        json.dump(mcp_config, f, indent=2)

    logger.info("MCP configuration created", config_file=str(config_file))
    return True


def create_supabase_client():
    """Create a Supabase client configuration."""
    project_root = Path(__file__).parent.parent

    # Create Supabase client utility
    supabase_client_code = '''"""
Supabase Client Configuration

Provides a configured Supabase client for database operations.
"""

import os
from typing import Optional

from supabase import create_client, Client
from dotenv import load_dotenv
import structlog

logger = structlog.get_logger(__name__)

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Global client instance
_supabase_client: Optional[Client] = None


def get_supabase_client(use_service_key: bool = False) -> Client:
    """
    Get a configured Supabase client.

    Args:
        use_service_key: If True, use service key for admin operations

    Returns:
        Configured Supabase client
    """
    global _supabase_client

    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable is required")

    # Choose appropriate key
    if use_service_key:
        if not SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_SERVICE_KEY environment variable is required for admin operations")
        key = SUPABASE_SERVICE_KEY
    else:
        if not SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_ANON_KEY environment variable is required")
        key = SUPABASE_ANON_KEY

    # Create client if not exists or if switching key types
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, key)
        logger.info("Supabase client created",
                   url=SUPABASE_URL,
                   key_type="service" if use_service_key else "anon")

    return _supabase_client


def test_connection() -> bool:
    """Test Supabase connection."""
    try:
        client = get_supabase_client()
        # Try a simple query to test connection
        result = client.table("_supabase_migrations").select("*").limit(1).execute()
        logger.info("Supabase connection test successful")
        return True
    except Exception as e:
        logger.error("Supabase connection test failed", error=str(e))
        return False


async def initialize_database():
    """Initialize database with required tables for ELF Automations."""
    try:
        client = get_supabase_client(use_service_key=True)

        # Create customers table
        customers_sql = """
        CREATE TABLE IF NOT EXISTS customers (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(50),
            company VARCHAR(255),
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        # Create leads table
        leads_sql = """
        CREATE TABLE IF NOT EXISTS leads (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            company VARCHAR(255),
            source VARCHAR(100),
            status VARCHAR(50) DEFAULT 'new',
            score INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        # Create tasks table
        tasks_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id BIGSERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            assignee VARCHAR(255),
            status VARCHAR(50) DEFAULT 'pending',
            priority VARCHAR(20) DEFAULT 'medium',
            due_date TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        # Create business_metrics table
        metrics_sql = """
        CREATE TABLE IF NOT EXISTS business_metrics (
            id BIGSERIAL PRIMARY KEY,
            metric_name VARCHAR(100) NOT NULL,
            metric_value DECIMAL(10,2) NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            period_start DATE,
            period_end DATE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        # Execute table creation
        tables = [
            ("customers", customers_sql),
            ("leads", leads_sql),
            ("tasks", tasks_sql),
            ("business_metrics", metrics_sql)
        ]

        for table_name, sql in tables:
            try:
                client.postgrest.rpc("exec_sql", {"sql": sql}).execute()
                logger.info(f"Table {table_name} created/verified")
            except Exception as e:
                logger.error(f"Failed to create table {table_name}", error=str(e))

        # Insert sample data
        await insert_sample_data(client)

        logger.info("Database initialization completed")
        return True

    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        return False


async def insert_sample_data(client: Client):
    """Insert sample data into tables."""
    try:
        # Sample customers
        customers_data = [
            {"name": "John Doe", "email": "john@example.com", "company": "Tech Corp", "status": "active"},
            {"name": "Jane Smith", "email": "jane@startup.io", "company": "Startup Inc", "status": "active"},
            {"name": "Bob Johnson", "email": "bob@enterprise.com", "company": "Enterprise Ltd", "status": "inactive"}
        ]

        # Sample leads
        leads_data = [
            {"name": "Alice Brown", "email": "alice@prospect.com", "company": "Prospect Co", "source": "website", "status": "qualified", "score": 85},
            {"name": "Charlie Wilson", "email": "charlie@potential.org", "company": "Potential Org", "source": "referral", "status": "new", "score": 65},
            {"name": "Diana Davis", "email": "diana@opportunity.net", "company": "Opportunity Net", "source": "social", "status": "contacted", "score": 75}
        ]

        # Sample tasks
        tasks_data = [
            {"title": "Follow up with Alice Brown", "description": "Schedule demo call", "assignee": "sales-agent-001", "status": "pending", "priority": "high"},
            {"title": "Prepare Q4 report", "description": "Compile quarterly business metrics", "assignee": "analytics-agent-001", "status": "in_progress", "priority": "medium"},
            {"title": "Update website content", "description": "Refresh product descriptions", "assignee": "marketing-agent-001", "status": "pending", "priority": "low"}
        ]

        # Sample metrics
        metrics_data = [
            {"metric_name": "monthly_revenue", "metric_value": 125000.00, "metric_type": "financial", "period_start": "2024-11-01", "period_end": "2024-11-30"},
            {"metric_name": "customer_acquisition_cost", "metric_value": 250.00, "metric_type": "marketing", "period_start": "2024-11-01", "period_end": "2024-11-30"},
            {"metric_name": "customer_satisfaction", "metric_value": 4.2, "metric_type": "service", "period_start": "2024-11-01", "period_end": "2024-11-30"},
            {"metric_name": "task_completion_rate", "metric_value": 0.92, "metric_type": "operational", "period_start": "2024-11-01", "period_end": "2024-11-30"}
        ]

        # Insert data with upsert to avoid duplicates
        datasets = [
            ("customers", customers_data),
            ("leads", leads_data),
            ("tasks", tasks_data),
            ("business_metrics", metrics_data)
        ]

        for table_name, data in datasets:
            try:
                client.table(table_name).upsert(data).execute()
                logger.info(f"Sample data inserted into {table_name}", count=len(data))
            except Exception as e:
                logger.error(f"Failed to insert sample data into {table_name}", error=str(e))

    except Exception as e:
        logger.error("Failed to insert sample data", error=str(e))
'''

    client_file = project_root / "utils" / "supabase_client.py"
    client_file.parent.mkdir(exist_ok=True)

    with open(client_file, "w") as f:
        f.write(supabase_client_code)

    logger.info("Supabase client utility created", file=str(client_file))
    return True


def update_requirements():
    """Update requirements.txt with Supabase dependencies."""
    project_root = Path(__file__).parent.parent
    requirements_file = project_root / "requirements.txt"

    # Read existing requirements
    existing_requirements = set()
    if requirements_file.exists():
        with open(requirements_file, "r") as f:
            existing_requirements = set(
                line.strip() for line in f if line.strip() and not line.startswith("#")
            )

    # Add Supabase dependencies
    supabase_deps = {"supabase>=2.0.0", "postgrest>=0.10.0"}

    # Combine with existing requirements
    all_requirements = existing_requirements.union(supabase_deps)

    # Write updated requirements
    with open(requirements_file, "w") as f:
        f.write("# ELF Automations Dependencies\\n\\n")
        for req in sorted(all_requirements):
            f.write(f"{req}\\n")

    logger.info("Requirements updated with Supabase dependencies")
    return True


async def test_supabase_integration():
    """Test the complete Supabase integration."""
    logger.info("Testing Supabase integration...")

    # Add project root to path for imports
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    try:
        from utils.supabase_client import (
            get_supabase_client,
            initialize_database,
            test_connection,
        )

        # Test connection
        if not test_connection():
            logger.error("Supabase connection test failed")
            return False

        # Initialize database
        if not await initialize_database():
            logger.error("Database initialization failed")
            return False

        # Test basic operations
        client = get_supabase_client()

        # Test read operation
        customers = client.table("customers").select("*").limit(3).execute()
        logger.info("Customers query successful", count=len(customers.data))

        # Test write operation
        test_customer = {
            "name": "Test Customer",
            "email": f"test_{int(asyncio.get_event_loop().time())}@example.com",
            "company": "Test Corp",
        }

        result = client.table("customers").insert(test_customer).execute()
        logger.info("Customer creation successful", customer_id=result.data[0]["id"])

        logger.info("✅ Supabase integration test completed successfully")
        return True

    except Exception as e:
        logger.error("Supabase integration test failed", error=str(e))
        return False


def main():
    """Main setup function."""
    logger.info("🗄️ ELF Automations Supabase Integration Setup")
    logger.info("=" * 60)

    # Load environment variables
    load_dotenv()

    # Check prerequisites
    if not check_node_npm():
        logger.error("Node.js and npm are required for Supabase MCP server")
        logger.info("Install Node.js from: https://nodejs.org/")
        return 1

    # Check Supabase environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
    access_token = (
        os.getenv("SUPABASE_ACCESS_TOKEN")
        or os.getenv("SUPABASE_PERSONAL_ACCESS_TOKEN")
        or os.getenv("SUPABASE_PAT")
    )

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {'*' * 8}...{value[-4:]}")
        else:
            logger.warning(f"❌ {var}: Not set")
            missing_vars.append(var)

    if access_token:
        logger.info(f"✅ Access Token: {'*' * 8}...{access_token[-4:]}")
    else:
        logger.warning(
            "❌ SUPABASE_ACCESS_TOKEN (or SUPABASE_PERSONAL_ACCESS_TOKEN): Not set"
        )
        missing_vars.append("SUPABASE_ACCESS_TOKEN")

    if missing_vars:
        logger.error("Missing required environment variables", missing=missing_vars)
        return 1

    logger.info("✅ Prerequisites check passed")

    try:
        # Install Supabase MCP server
        if not install_supabase_mcp():
            logger.error("Failed to install Supabase MCP server")
            return 1

        # Create MCP configuration
        if not create_mcp_config():
            logger.error("Failed to create MCP configuration")
            return 1

        # Create Supabase client utility
        if not create_supabase_client():
            logger.error("Failed to create Supabase client utility")
            return 1

        # Update requirements
        if not update_requirements():
            logger.error("Failed to update requirements")
            return 1

        # Install Python dependencies
        logger.info("Installing Python dependencies...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error("Failed to install Python dependencies", error=result.stderr)
            return 1

        # Test integration
        success = asyncio.run(test_supabase_integration())

        if success:
            logger.info("🚀 Supabase integration setup completed successfully!")
            logger.info("Configuration files created:")
            logger.info("  - config/mcp_config.json (MCP server configuration)")
            logger.info("  - utils/supabase_client.py (Python client utility)")
            logger.info("  - requirements.txt (updated with Supabase dependencies)")
            logger.info("\\nNext steps:")
            logger.info("  1. Run test scripts to verify integration")
            logger.info("  2. Update your MCP client configuration")
            logger.info("  3. Test AI agent interactions with Supabase")
            return 0
        else:
            logger.error("Supabase integration test failed")
            return 1

    except Exception as e:
        logger.error("Setup failed", error=str(e))
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
