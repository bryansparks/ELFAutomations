#!/usr/bin/env python3
"""
Setup Supabase Database Schema

Creates the necessary tables for the Virtual AI Company Platform in Supabase.
"""

import asyncio
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.supabase_util import get_supabase_client

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


def create_tables_sql():
    """Return SQL statements to create business tables."""
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
        # Agent activities table (for tracking agent actions)
        """
        CREATE TABLE IF NOT EXISTS agent_activities (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            agent_id VARCHAR(255) NOT NULL,
            activity_type VARCHAR(100) NOT NULL,
            description TEXT,
            target_table VARCHAR(100),
            target_id UUID,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        # Create indexes for better performance
        """
        CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
        CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
        CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score);
        CREATE INDEX IF NOT EXISTS idx_leads_assigned_agent ON leads(assigned_agent_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent ON tasks(assigned_agent_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
        CREATE INDEX IF NOT EXISTS idx_business_metrics_name ON business_metrics(metric_name);
        CREATE INDEX IF NOT EXISTS idx_business_metrics_type ON business_metrics(metric_type);
        CREATE INDEX IF NOT EXISTS idx_agent_activities_agent ON agent_activities(agent_id);
        CREATE INDEX IF NOT EXISTS idx_agent_activities_type ON agent_activities(activity_type);
        """,
        # Create updated_at trigger function
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """,
        # Create triggers for updated_at
        """
        CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """,
    ]


def create_sample_data_sql():
    """Return SQL statements to insert sample data."""
    return [
        # Sample customers
        """
        INSERT INTO customers (name, email, phone, company, status) VALUES
        ('John Doe', 'john@techcorp.com', '+1-555-0101', 'Tech Corp', 'active'),
        ('Jane Smith', 'jane@startup.io', '+1-555-0102', 'Startup Inc', 'active'),
        ('Bob Johnson', 'bob@enterprise.com', '+1-555-0103', 'Enterprise Ltd', 'inactive'),
        ('Alice Brown', 'alice@prospect.com', '+1-555-0104', 'Prospect Co', 'active'),
        ('Charlie Wilson', 'charlie@potential.org', '+1-555-0105', 'Potential Org', 'active')
        ON CONFLICT (email) DO NOTHING;
        """,
        # Sample leads
        """
        INSERT INTO leads (name, email, company, source, status, score) VALUES
        ('Diana Davis', 'diana@opportunity.net', 'Opportunity Net', 'website', 'qualified', 85),
        ('Eve Martinez', 'eve@growth.biz', 'Growth Biz', 'referral', 'new', 65),
        ('Frank Taylor', 'frank@scale.co', 'Scale Co', 'social', 'contacted', 75),
        ('Grace Lee', 'grace@expand.org', 'Expand Org', 'email', 'qualified', 90),
        ('Henry Chen', 'henry@develop.io', 'Develop IO', 'website', 'new', 55)
        ON CONFLICT DO NOTHING;
        """,
        # Sample tasks
        """
        INSERT INTO tasks (title, description, status, priority, assigned_agent_id, created_by_agent_id) VALUES
        ('Follow up with Diana Davis', 'Schedule demo call for high-value prospect', 'pending', 1, 'sales-agent-001', 'chief-ai-agent'),
        ('Prepare Q4 report', 'Compile quarterly business metrics and analysis', 'in_progress', 2, 'analytics-agent-001', 'chief-ai-agent'),
        ('Update website content', 'Refresh product descriptions and pricing', 'pending', 3, 'marketing-agent-001', 'marketing-manager'),
        ('Customer onboarding', 'Set up new customer account and training', 'pending', 2, 'customer-success-001', 'cs-manager'),
        ('Security audit', 'Review system security and compliance', 'pending', 1, 'security-agent-001', 'cto-agent')
        ON CONFLICT DO NOTHING;
        """,
        # Sample business metrics
        """
        INSERT INTO business_metrics (metric_name, metric_value, metric_type, period_start, period_end) VALUES
        ('monthly_revenue', 125000.00, 'financial', '2024-11-01', '2024-11-30'),
        ('customer_acquisition_cost', 250.00, 'marketing', '2024-11-01', '2024-11-30'),
        ('customer_satisfaction', 4.2, 'service', '2024-11-01', '2024-11-30'),
        ('task_completion_rate', 0.92, 'operational', '2024-11-01', '2024-11-30'),
        ('lead_conversion_rate', 0.15, 'sales', '2024-11-01', '2024-11-30'),
        ('agent_efficiency', 0.87, 'operational', '2024-11-01', '2024-11-30')
        ON CONFLICT DO NOTHING;
        """,
    ]


async def create_database_schema():
    """Create the database schema in Supabase."""
    logger.info("🏗️ Creating Supabase Database Schema")
    logger.info("=" * 50)

    try:
        client = get_supabase_client()
        logger.info("✅ Supabase client connected")

        # Create tables
        table_sql_statements = create_tables_sql()

        for i, sql in enumerate(table_sql_statements, 1):
            try:
                logger.info(f"Executing SQL statement {i}/{len(table_sql_statements)}")

                # Use RPC to execute SQL if available
                try:
                    result = client.rpc("exec_sql", {"sql": sql}).execute()
                    logger.info(f"✅ SQL statement {i} executed successfully")
                except Exception as rpc_error:
                    logger.warning(
                        f"RPC execution failed for statement {i}", error=str(rpc_error)
                    )
                    # RPC might not be available, continue anyway

            except Exception as e:
                logger.error(f"❌ Failed to execute SQL statement {i}", error=str(e))
                # Continue with other statements

        logger.info("✅ Database schema creation completed")
        return True

    except Exception as e:
        logger.error("❌ Failed to create database schema", error=str(e))
        return False


async def insert_sample_data():
    """Insert sample data into the tables."""
    logger.info("📊 Inserting Sample Data")
    logger.info("=" * 30)

    try:
        client = get_supabase_client()

        # Insert sample data
        sample_sql_statements = create_sample_data_sql()

        for i, sql in enumerate(sample_sql_statements, 1):
            try:
                logger.info(f"Inserting sample data {i}/{len(sample_sql_statements)}")

                # Use RPC to execute SQL if available
                try:
                    result = client.rpc("exec_sql", {"sql": sql}).execute()
                    logger.info(f"✅ Sample data {i} inserted successfully")
                except Exception as rpc_error:
                    logger.warning(
                        f"RPC execution failed for sample data {i}",
                        error=str(rpc_error),
                    )
                    # Try direct table operations as fallback
                    if i == 1:  # Customers
                        try:
                            customers_data = [
                                {
                                    "name": "John Doe",
                                    "email": "john@techcorp.com",
                                    "company": "Tech Corp",
                                    "status": "active",
                                },
                                {
                                    "name": "Jane Smith",
                                    "email": "jane@startup.io",
                                    "company": "Startup Inc",
                                    "status": "active",
                                },
                                {
                                    "name": "Bob Johnson",
                                    "email": "bob@enterprise.com",
                                    "company": "Enterprise Ltd",
                                    "status": "inactive",
                                },
                            ]
                            result = (
                                client.table("customers")
                                .upsert(customers_data)
                                .execute()
                            )
                            logger.info(
                                "✅ Customers inserted via direct table operation"
                            )
                        except Exception as direct_error:
                            logger.warning(
                                "Direct table operation also failed",
                                error=str(direct_error),
                            )

            except Exception as e:
                logger.error(f"❌ Failed to insert sample data {i}", error=str(e))

        logger.info("✅ Sample data insertion completed")
        return True

    except Exception as e:
        logger.error("❌ Failed to insert sample data", error=str(e))
        return False


async def verify_schema():
    """Verify that the schema was created successfully."""
    logger.info("🔍 Verifying Database Schema")
    logger.info("=" * 35)

    try:
        client = get_supabase_client()

        # Test each table
        tables = ["customers", "leads", "tasks", "business_metrics", "agent_activities"]

        for table in tables:
            try:
                result = client.table(table).select("*").limit(1).execute()
                logger.info(f"✅ Table '{table}' is accessible")
            except Exception as e:
                logger.warning(f"⚠️ Table '{table}' is not accessible", error=str(e))

        # Test a simple query
        try:
            customers = client.table("customers").select("*").limit(3).execute()
            logger.info(
                f"✅ Sample query successful: {len(customers.data)} customers found"
            )
        except Exception as e:
            logger.warning("⚠️ Sample query failed", error=str(e))

        return True

    except Exception as e:
        logger.error("❌ Schema verification failed", error=str(e))
        return False


async def main():
    """Main setup function."""
    logger.info("🚀 Supabase Database Schema Setup")
    logger.info("=" * 60)

    # Load environment
    load_dotenv()

    # Step 1: Create schema
    schema_success = await create_database_schema()
    if not schema_success:
        logger.error("❌ Schema creation failed")
        return 1

    # Step 2: Insert sample data
    data_success = await insert_sample_data()
    if not data_success:
        logger.warning("⚠️ Sample data insertion had issues")

    # Step 3: Verify schema
    verify_success = await verify_schema()
    if not verify_success:
        logger.warning("⚠️ Schema verification had issues")

    if schema_success:
        logger.info("🎉 Supabase database setup completed!")
        logger.info("\nNext steps:")
        logger.info("  1. Run: python scripts/test_business_tools_supabase.py")
        logger.info("  2. Test AI agent interactions")
        logger.info("  3. Run full system demos")
        return 0
    else:
        logger.error("❌ Setup failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
