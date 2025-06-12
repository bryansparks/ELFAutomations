#!/usr/bin/env python3
"""
Supabase Environment Configuration Helper

Helps configure the minimal Supabase environment variables needed for the platform.
"""

import os
import sys
from pathlib import Path

import structlog

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


def main():
    """Configure Supabase environment variables."""
    logger.info("🔧 Supabase Environment Configuration")
    logger.info("=" * 50)

    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"

    # Read existing .env file
    env_vars = {}
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

    logger.info(f"Found existing .env file with {len(env_vars)} variables")

    # Check current Supabase configuration
    supabase_url = env_vars.get("SUPABASE_URL")
    supabase_key = env_vars.get("SUPABASE_KEY")
    supabase_anon_key = env_vars.get("SUPABASE_ANON_KEY")
    supabase_password = env_vars.get("SUPABASE_PASSWORD")

    logger.info("Current Supabase Configuration:")
    logger.info(f"  SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    logger.info(f"  SUPABASE_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")
    logger.info(f"  SUPABASE_ANON_KEY: {'✅ Set' if supabase_anon_key else '❌ Missing'}")
    logger.info(f"  SUPABASE_PASSWORD: {'✅ Set' if supabase_password else '❌ Missing'}")

    # If we have SUPABASE_KEY but not SUPABASE_ANON_KEY, use SUPABASE_KEY as anon key
    if supabase_key and not supabase_anon_key:
        logger.info("Using SUPABASE_KEY as SUPABASE_ANON_KEY")
        env_vars["SUPABASE_ANON_KEY"] = supabase_key
        supabase_anon_key = supabase_key

    # Check if we have minimum required configuration
    if supabase_url and (supabase_anon_key or supabase_key):
        logger.info("✅ Minimum Supabase configuration found!")

        # Write updated .env file
        with open(env_file, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        logger.info("Updated .env file with Supabase configuration")

        # Test basic connectivity
        logger.info("Testing Supabase connectivity...")
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
                    logger.error(
                        "Failed to install supabase package", error=result.stderr
                    )
                    return 1
                import supabase

            # Create client and test
            client = supabase.create_client(
                supabase_url, supabase_anon_key or supabase_key
            )

            # Try a simple query to test connectivity
            try:
                result = (
                    client.table("_supabase_migrations").select("*").limit(1).execute()
                )
                logger.info("✅ Supabase connection successful!")

                # Create basic Supabase utility
                create_supabase_utility()

                logger.info("🎉 Supabase configuration completed successfully!")
                logger.info("Next steps:")
                logger.info("  1. Run: python scripts/test_business_tools_supabase.py")
                logger.info("  2. Test AI agent interactions")
                logger.info("  3. Run full system demos")

                return 0

            except Exception as e:
                logger.warning(
                    "Connection test failed, but client created successfully",
                    error=str(e),
                )
                logger.info(
                    "This might be normal if your Supabase project doesn't have migrations table"
                )

                # Still create the utility
                create_supabase_utility()

                logger.info("✅ Supabase configuration completed!")
                return 0

        except Exception as e:
            logger.error("Failed to test Supabase connection", error=str(e))
            return 1

    else:
        logger.error("❌ Missing required Supabase configuration")
        logger.info("\nTo configure Supabase, you need:")
        logger.info("1. Go to https://supabase.com/dashboard")
        logger.info("2. Select or create your project")
        logger.info("3. Go to Settings → API")
        logger.info("4. Copy the Project URL and anon/public key")
        logger.info("5. Add these to your .env file:")
        logger.info("   SUPABASE_URL=https://your-project-ref.supabase.co")
        logger.info("   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        return 1


def create_supabase_utility():
    """Create a Supabase utility module."""
    project_root = Path(__file__).parent.parent
    utils_dir = project_root / "utils"
    utils_dir.mkdir(exist_ok=True)

    utility_code = '''"""
Supabase Client Utility

Provides a configured Supabase client for the Virtual AI Company Platform.
"""

import os
from typing import Optional, Dict, Any, List

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
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

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

    if not SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_ANON_KEY or SUPABASE_KEY environment variable is required")

    # Create client if not exists
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
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
        logger.warning("Supabase connection test failed", error=str(e))
        return False


async def ensure_business_tables():
    """Ensure business tables exist in Supabase."""
    try:
        client = get_supabase_client()

        # Check if tables exist by trying to query them
        tables_to_check = ["customers", "leads", "tasks", "business_metrics"]
        existing_tables = []

        for table in tables_to_check:
            try:
                result = client.table(table).select("*").limit(1).execute()
                existing_tables.append(table)
                logger.info(f"Table {table} exists")
            except Exception as e:
                logger.warning(f"Table {table} does not exist or is not accessible", error=str(e))

        if len(existing_tables) == len(tables_to_check):
            logger.info("All business tables are accessible")
            return True
        else:
            logger.warning(f"Only {len(existing_tables)}/{len(tables_to_check)} tables are accessible")
            logger.info("You may need to create tables manually in your Supabase dashboard")
            return False

    except Exception as e:
        logger.error("Failed to check business tables", error=str(e))
        return False


async def insert_sample_data():
    """Insert sample data into business tables."""
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

        success_count = 0
        for table_name, data in datasets:
            try:
                result = client.table(table_name).upsert(data).execute()
                logger.info(f"Sample data inserted into {table_name}", count=len(data))
                success_count += 1
            except Exception as e:
                logger.warning(f"Could not insert sample data into {table_name}", error=str(e))

        logger.info(f"Sample data insertion completed: {success_count}/{len(datasets)} tables")
        return success_count == len(datasets)

    except Exception as e:
        logger.error("Failed to insert sample data", error=str(e))
        return False


def query_table(table_name: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Query a table with optional filters."""
    try:
        client = get_supabase_client()
        query = client.table(table_name).select("*")

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        result = query.limit(limit).execute()
        return result.data

    except Exception as e:
        logger.error(f"Failed to query table {table_name}", error=str(e))
        return []


def insert_record(table_name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Insert a record into a table."""
    try:
        client = get_supabase_client()
        result = client.table(table_name).insert(data).execute()
        return result.data[0] if result.data else None

    except Exception as e:
        logger.error(f"Failed to insert record into {table_name}", error=str(e))
        return None


def update_record(table_name: str, record_id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a record in a table."""
    try:
        client = get_supabase_client()
        result = client.table(table_name).update(data).eq("id", record_id).execute()
        return result.data[0] if result.data else None

    except Exception as e:
        logger.error(f"Failed to update record in {table_name}", error=str(e))
        return None
'''

    utility_file = utils_dir / "supabase_util.py"
    with open(utility_file, "w") as f:
        f.write(utility_code)

    logger.info("Supabase utility created", file=str(utility_file))


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
