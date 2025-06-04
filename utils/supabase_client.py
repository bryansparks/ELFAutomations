"""
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
