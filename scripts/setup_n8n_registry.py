#!/usr/bin/env python3
"""
Setup N8N Workflow Registry in Supabase

This script creates the necessary tables and views for the N8N workflow registry.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Debug: Check if variables are loaded
print(f"Loading .env from: {env_path}")
if not os.getenv('SUPABASE_URL'):
    print("Warning: SUPABASE_URL not found in environment after loading .env")

def setup_n8n_registry():
    """Create N8N workflow registry schema in Supabase"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    # Try different possible key names
    supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_SECRET_KEY')
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        print(f"Looked for .env at: {env_path}")
        print("\nPlease ensure your .env file contains:")
        print("SUPABASE_URL=your-supabase-url")
        print("SUPABASE_KEY=your-supabase-key (or SUPABASE_ANON_KEY)")
        sys.exit(1)
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Read SQL file
    sql_file = Path(__file__).parent.parent / 'sql' / 'create_n8n_workflow_registry.sql'
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Execute SQL
    try:
        # Split into individual statements
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        for statement in statements:
            if statement and not statement.startswith('--'):
                print(f"Executing: {statement[:50]}...")
                # Note: Supabase doesn't directly support raw SQL execution
                # You'll need to run this SQL directly in Supabase SQL Editor
                print("Please run the following SQL in Supabase SQL Editor:")
                print("-" * 80)
                print(statement + ";")
                print("-" * 80)
                print()
        
        print("\nSUCCESS: Please copy and run the above SQL statements in your Supabase SQL Editor")
        print("Navigate to: https://app.supabase.com/project/[your-project]/sql/new")
        print("\nAlternatively, you can run the entire SQL file at once:")
        print(f"Copy contents from: {sql_file}")
        
        # Test connection
        print("\nTesting Supabase connection...")
        # Try to query a simple table
        try:
            result = supabase.table('n8n_workflows').select('count').execute()
            print("✓ Successfully connected to Supabase")
            print(f"  Found {result.data[0]['count'] if result.data else 0} workflows")
        except Exception as e:
            print("! Tables don't exist yet. Please run the SQL first.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def verify_setup():
    """Verify the N8N registry is properly set up"""
    
    # Ensure .env is loaded
    if not os.getenv('SUPABASE_URL'):
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(dotenv_path=env_path)
    
    supabase_url = os.getenv('SUPABASE_URL')
    # Try different possible key names
    supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_SECRET_KEY')
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        print(f"Looked for .env at: {Path(__file__).parent.parent / '.env'}")
        return False
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Check if tables exist
        tables_to_check = ['n8n_workflows', 'workflow_executions']
        
        for table in tables_to_check:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                print(f"✓ Table '{table}' exists")
            except Exception as e:
                print(f"✗ Table '{table}' not found: {e}")
                return False
        
        # Check views
        print("\nNote: Views cannot be checked via API, verify in Supabase dashboard:")
        print("- workflow_execution_stats")
        print("- recent_workflow_executions")
        
        return True
        
    except Exception as e:
        print(f"Error verifying setup: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup N8N Workflow Registry')
    parser.add_argument('--verify', action='store_true', help='Verify setup only')
    
    args = parser.parse_args()
    
    if args.verify:
        if verify_setup():
            print("\n✅ N8N Registry setup verified!")
        else:
            print("\n❌ N8N Registry setup incomplete")
    else:
        setup_n8n_registry()