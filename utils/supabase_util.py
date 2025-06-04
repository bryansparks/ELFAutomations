"""
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
