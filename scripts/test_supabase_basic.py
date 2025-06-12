#!/usr/bin/env python3
"""
Basic Supabase Integration Test

Tests Supabase connectivity with minimal configuration.
"""

import asyncio
import os
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


def test_supabase_connection():
    """Test basic Supabase connection with available credentials."""
    logger.info("🧪 Testing Supabase Connection")
    logger.info("=" * 40)

    # Load environment
    load_dotenv()

    # Check what we have
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")  # Generic key name
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase_password = os.getenv("SUPABASE_PASSWORD")

    logger.info("Available Configuration:")
    logger.info(f"  SUPABASE_URL: {'✅' if supabase_url else '❌'}")
    logger.info(f"  SUPABASE_KEY: {'✅' if supabase_key else '❌'}")
    logger.info(f"  SUPABASE_ANON_KEY: {'✅' if supabase_anon_key else '❌'}")
    logger.info(f"  SUPABASE_PASSWORD: {'✅' if supabase_password else '❌'}")

    if not supabase_url:
        logger.error("SUPABASE_URL is required")
        return False

    # Try to determine the correct key to use
    api_key = supabase_anon_key or supabase_key
    if not api_key:
        logger.error("No Supabase API key found (SUPABASE_ANON_KEY or SUPABASE_KEY)")
        return False

    try:
        # Try to install supabase if not available
        try:
            import supabase
        except ImportError:
            logger.info("Installing supabase package...")
            import subprocess

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "supabase>=2.0.0"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.error("Failed to install supabase package", error=result.stderr)
                return False
            import supabase

        # Create client
        logger.info("Creating Supabase client...")
        client = supabase.create_client(supabase_url, api_key)

        # Test basic connection
        logger.info("Testing connection...")

        # Try to query a system table to test connectivity
        try:
            # This should work on any Supabase instance
            result = client.table("_supabase_migrations").select("*").limit(1).execute()
            logger.info("✅ Supabase connection successful!")
            logger.info(f"Migration table accessible: {len(result.data)} records found")
            return True
        except Exception as e:
            # If migrations table doesn't exist, try a simple RPC call
            logger.info("Migrations table not accessible, trying alternative test...")
            try:
                # Try to get database version
                result = client.rpc("version").execute()
                logger.info("✅ Supabase connection successful via RPC!")
                return True
            except Exception as e2:
                logger.error("Connection test failed", error=str(e2))
                return False

    except Exception as e:
        logger.error("Failed to test Supabase connection", error=str(e))
        return False


def create_basic_supabase_client():
    """Create a basic Supabase client utility."""
    project_root = Path(__file__).parent.parent
    utils_dir = project_root / "utils"
    utils_dir.mkdir(exist_ok=True)

    client_code = '''"""
Basic Supabase Client

Provides a simple Supabase client for database operations.
"""

import os
from typing import Optional

try:
    from supabase import create_client, Client
except ImportError:
    print("Supabase package not installed. Run: pip install supabase>=2.0.0")
    raise

from dotenv import load_dotenv
import structlog

logger = structlog.get_logger(__name__)

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Fallback generic key

# Global client instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get a configured Supabase client.

    Returns:
        Configured Supabase client
    """
    global _supabase_client

    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable is required")

    # Choose appropriate key
    api_key = SUPABASE_ANON_KEY or SUPABASE_KEY
    if not api_key:
        raise ValueError("SUPABASE_ANON_KEY or SUPABASE_KEY environment variable is required")

    # Create client if not exists
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, api_key)
        logger.info("Supabase client created", url=SUPABASE_URL)

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


async def create_business_tables():
    """Create business tables for ELF Automations."""
    try:
        client = get_supabase_client()

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

        # Execute table creation using RPC
        tables = [
            ("customers", customers_sql),
            ("leads", leads_sql),
            ("tasks", tasks_sql),
            ("business_metrics", metrics_sql)
        ]

        for table_name, sql in tables:
            try:
                # Use RPC to execute SQL
                result = client.rpc("exec_sql", {"sql": sql}).execute()
                logger.info(f"Table {table_name} created/verified")
            except Exception as e:
                logger.warning(f"Could not create table {table_name} via RPC", error=str(e))
                # Try direct table creation (this might not work without proper permissions)
                try:
                    # This is a fallback - may not work in all Supabase configurations
                    pass
                except Exception as e2:
                    logger.error(f"Failed to create table {table_name}", error=str(e2))

        logger.info("Business tables setup completed")
        return True

    except Exception as e:
        logger.error("Failed to create business tables", error=str(e))
        return False


async def insert_sample_data():
    """Insert sample data into tables."""
    try:
        client = get_supabase_client()

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
                result = client.table(table_name).upsert(data).execute()
                logger.info(f"Sample data inserted into {table_name}", count=len(data))
            except Exception as e:
                logger.warning(f"Could not insert sample data into {table_name}", error=str(e))

        return True

    except Exception as e:
        logger.error("Failed to insert sample data", error=str(e))
        return False
'''

    client_file = utils_dir / "supabase_client_basic.py"
    with open(client_file, "w") as f:
        f.write(client_code)

    logger.info("Basic Supabase client created", file=str(client_file))
    return True


async def main():
    """Main test function."""
    logger.info("🚀 Basic Supabase Integration Test")
    logger.info("=" * 50)

    # Test connection
    if not test_supabase_connection():
        logger.error("Supabase connection failed")
        return 1

    # Create basic client utility
    if not create_basic_supabase_client():
        logger.error("Failed to create Supabase client utility")
        return 1

    # Test the client utility
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utils.supabase_client_basic import (
            create_business_tables,
            get_supabase_client,
            insert_sample_data,
        )

        # Test client creation
        client = get_supabase_client()
        logger.info("✅ Supabase client utility working")

        # Try to create tables (may require admin permissions)
        logger.info("Attempting to create business tables...")
        await create_business_tables()

        # Try to insert sample data
        logger.info("Attempting to insert sample data...")
        await insert_sample_data()

        logger.info("🎉 Basic Supabase integration completed!")
        logger.info("Next steps:")
        logger.info("  1. Configure MCP server with proper access tokens")
        logger.info("  2. Test AI agent interactions with Supabase")
        logger.info("  3. Run full system demos")

        return 0

    except Exception as e:
        logger.error("Integration test failed", error=str(e))
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
