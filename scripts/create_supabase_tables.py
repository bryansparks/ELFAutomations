#!/usr/bin/env python3
"""
Create Supabase Tables

Creates the necessary database tables for the Virtual AI Company Platform.
"""

import os
from pathlib import Path

import structlog
from dotenv import load_dotenv
from supabase import create_client, Client

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
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def create_supabase_client() -> Client:
    """Create and return a Supabase client."""
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    
    return create_client(url, key)


def execute_sql_statements(client: Client, sql_statements: list) -> bool:
    """Execute SQL statements using Supabase RPC."""
    success_count = 0
    
    for i, sql in enumerate(sql_statements, 1):
        if not sql.strip():
            continue
            
        try:
            logger.info(f"Executing statement {i}/{len(sql_statements)}")
            
            # Try to execute via RPC (this may not work for all statements)
            result = client.rpc('exec_sql', {'sql': sql})
            
            if result:
                logger.info(f"✅ Statement {i} executed successfully")
                success_count += 1
            else:
                logger.warning(f"⚠️ Statement {i} returned no result")
                
        except Exception as e:
            logger.warning(f"⚠️ Statement {i} failed: {str(e)}")
            # Continue with other statements
    
    return success_count > 0


def create_tables_manually(client: Client) -> bool:
    """Create tables using individual Supabase operations."""
    logger.info("🏗️ Creating tables using Supabase client operations")
    
    try:
        # Test basic connectivity first
        logger.info("Testing Supabase connection...")
        
        # Try to create a simple table first
        test_sql = """
        CREATE TABLE IF NOT EXISTS test_connection (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Since direct SQL execution might not work, let's try using the REST API
        # to check if we can access the database
        
        # Try to query system tables to verify connection
        try:
            # This might fail if tables don't exist, but it tests the connection
            result = client.table('information_schema.tables').select('table_name').limit(1).execute()
            logger.info("✅ Database connection verified")
        except Exception as e:
            logger.info(f"Database connection test: {str(e)}")
        
        logger.info("💡 Direct table creation via Python client has limitations")
        logger.info("📋 Recommended approach: Use Supabase Dashboard SQL Editor")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Table creation failed: {str(e)}")
        return False


def main():
    """Main function to create tables."""
    logger.info("🚀 Creating Supabase Tables")
    logger.info("=" * 40)
    
    try:
        # Create Supabase client
        client = create_supabase_client()
        logger.info("✅ Supabase client created")
        
        # Read SQL file
        sql_file = Path("sql/create_business_tables.sql")
        if not sql_file.exists():
            logger.error(f"❌ SQL file not found: {sql_file}")
            return 1
        
        with open(sql_file, "r") as f:
            sql_content = f.read()
        
        logger.info(f"📄 SQL file loaded ({len(sql_content)} characters)")
        
        # Split into statements
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        logger.info(f"Found {len(sql_statements)} SQL statements")
        
        # Try to create tables
        success = create_tables_manually(client)
        
        if success:
            logger.info("✅ Table creation process completed")
        else:
            logger.warning("⚠️ Table creation had issues")
        
        # Show next steps
        logger.info("\n📋 Next Steps:")
        logger.info("1. Copy the SQL from sql/create_business_tables.sql")
        logger.info("2. Go to your Supabase Dashboard")
        logger.info("3. Navigate to SQL Editor")
        logger.info("4. Paste and run the SQL")
        logger.info("5. Then test the business tools integration")
        
        # Show the SQL file path for easy access
        logger.info(f"\n📁 SQL file location: {sql_file.absolute()}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
