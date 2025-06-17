#!/usr/bin/env python3
"""
Verify and fix the workflow registry schema in Supabase
Checks for duplicate or incorrect schema elements from multiple applications
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Create Supabase client from environment variables"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)
    
    return create_client(url, key)

def check_schema():
    """Check the current schema and identify issues"""
    print("Verifying Workflow Registry Schema...")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Expected tables
    expected_tables = [
        'workflow_registry',
        'workflow_executions',
        'workflow_templates',
        'workflow_approvals'
    ]
    
    # Expected columns for workflow_registry
    expected_columns = {
        'workflow_registry': [
            'id', 'n8n_workflow_id', 'n8n_workflow_name', 'description',
            'category', 'version', 'status', 'configured_at', 'configured_by',
            'last_modified', 'owner_team', 'allowed_teams', 'webhook_url',
            'input_schema', 'output_schema', 'configuration',
            'avg_execution_time_ms', 'success_rate', 'last_execution',
            'execution_count', 'tags', 'created_at', 'updated_at'
        ],
        'workflow_executions': [
            'id', 'workflow_id', 'execution_id', 'triggered_by',
            'trigger_method', 'status', 'started_at', 'completed_at',
            'duration_ms', 'input_data', 'output_data', 'error_message',
            'team_request_id', 'created_at'
        ]
    }
    
    # Check tables
    print("\n1. Checking Tables:")
    print("-" * 40)
    
    for table in expected_tables:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            print(f"✓ Table '{table}' exists")
        except Exception as e:
            print(f"✗ Table '{table}' missing or error: {str(e)[:50]}")
    
    # Check columns for main tables
    print("\n2. Checking Column Structure:")
    print("-" * 40)
    
    for table, columns in expected_columns.items():
        try:
            # Get one row to check columns
            result = supabase.table(table).select("*").limit(1).execute()
            
            if result.data:
                actual_columns = set(result.data[0].keys())
                expected_set = set(columns)
                
                missing = expected_set - actual_columns
                extra = actual_columns - expected_set
                
                if missing:
                    print(f"\n✗ Table '{table}' missing columns: {missing}")
                if extra:
                    print(f"⚠ Table '{table}' has extra columns: {extra}")
                if not missing and not extra:
                    print(f"✓ Table '{table}' has correct columns")
            else:
                # Table exists but is empty, check another way
                print(f"⚠ Table '{table}' is empty, cannot verify columns")
                
        except Exception as e:
            print(f"✗ Cannot check '{table}': {str(e)[:50]}")
    
    # Check for duplicate tables (from earlier version)
    print("\n3. Checking for Duplicate Tables:")
    print("-" * 40)
    
    # Tables from the earlier version that might exist
    old_tables = [
        'n8n_workflow_registry',
        'n8n_workflow_executions',
        'n8n_workflow_errors',
        'n8n_workflow_metrics'
    ]
    
    for table in old_tables:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            print(f"⚠ Found old table '{table}' - consider migrating data")
        except:
            print(f"✓ Old table '{table}' not found (good)")
    
    # Check functions
    print("\n4. Checking Functions:")
    print("-" * 40)
    
    expected_functions = [
        'register_workflow',
        'approve_workflow',
        'activate_workflow',
        'record_workflow_execution'
    ]
    
    print("Note: Cannot check functions via Supabase client.")
    print("Run this SQL to verify functions:")
    print("""
    SELECT routine_name 
    FROM information_schema.routines 
    WHERE routine_type = 'FUNCTION' 
    AND routine_schema = 'public'
    AND routine_name IN ('register_workflow', 'approve_workflow', 'activate_workflow', 'record_workflow_execution');
    """)
    
    # Check views
    print("\n5. Checking Views:")
    print("-" * 40)
    
    expected_views = [
        'active_workflows',
        'workflow_performance',
        'team_workflow_usage'
    ]
    
    for view in expected_views:
        try:
            result = supabase.table(view).select("*").limit(1).execute()
            print(f"✓ View '{view}' exists")
        except:
            print(f"✗ View '{view}' missing")
    
    # Check for data in tables
    print("\n6. Checking Data:")
    print("-" * 40)
    
    for table in ['workflow_registry', 'workflow_executions']:
        try:
            result = supabase.table(table).select("count", count='exact').execute()
            count = result.count if hasattr(result, 'count') else 0
            print(f"Table '{table}' has {count} rows")
        except:
            print(f"Cannot count rows in '{table}'")

def generate_fix_script():
    """Generate SQL to fix any issues"""
    print("\n" + "=" * 60)
    print("Fix Script:")
    print("=" * 60)
    
    fix_sql = """
-- Fix Script for Workflow Registry Schema

-- 1. Drop old tables if they exist (backup data first!)
DROP TABLE IF EXISTS n8n_workflow_metrics CASCADE;
DROP TABLE IF EXISTS n8n_workflow_errors CASCADE;
DROP TABLE IF EXISTS n8n_workflow_executions CASCADE;
DROP TABLE IF EXISTS n8n_workflow_registry CASCADE;

-- 2. Ensure UUID extension is enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 3. Check if types exist before creating
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'workflow_status') THEN
        CREATE TYPE workflow_status AS ENUM (
            'draft', 'testing', 'configured', 'running', 'paused', 'deprecated'
        );
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'workflow_category') THEN
        CREATE TYPE workflow_category AS ENUM (
            'customer_onboarding', 'order_processing', 'data_sync', 
            'reporting', 'marketing_automation', 'team_coordination',
            'maintenance', 'integration', 'other'
        );
    END IF;
END$$;

-- 4. Verify main tables exist with correct structure
-- If tables already exist, this won't harm them
-- Run the full create_workflow_registry.sql if tables are missing

-- 5. Test the schema
SELECT 
    t.table_name,
    COUNT(c.column_name) as column_count
FROM information_schema.tables t
LEFT JOIN information_schema.columns c 
    ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
    AND t.table_name IN ('workflow_registry', 'workflow_executions', 
                         'workflow_templates', 'workflow_approvals')
GROUP BY t.table_name
ORDER BY t.table_name;

-- 6. Verify functions exist
SELECT routine_name, routine_type
FROM information_schema.routines 
WHERE routine_schema = 'public'
    AND routine_name IN ('register_workflow', 'approve_workflow', 
                         'activate_workflow', 'record_workflow_execution');

-- 7. Verify views exist
SELECT table_name 
FROM information_schema.views
WHERE table_schema = 'public'
    AND table_name IN ('active_workflows', 'workflow_performance', 'team_workflow_usage');
"""
    
    print(fix_sql)
    
    # Save fix script
    fix_file = Path(__file__).parent.parent / 'sql' / 'fix_workflow_schema.sql'
    with open(fix_file, 'w') as f:
        f.write(fix_sql)
    
    print(f"\nFix script saved to: {fix_file}")
    print("\nTo apply fixes:")
    print(f"1. Review the script: {fix_file}")
    print("2. Backup any existing data")
    print("3. Run in Supabase SQL editor or via psql")

def test_operations():
    """Test basic operations to ensure schema works"""
    print("\n" + "=" * 60)
    print("Testing Operations:")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    try:
        # Test 1: Insert a workflow
        print("\n1. Testing workflow insertion...")
        test_workflow = {
            'n8n_workflow_id': 'schema-test-001',
            'n8n_workflow_name': 'Schema Test Workflow',
            'description': 'Test workflow for schema verification',
            'category': 'other',
            'owner_team': 'test-team',
            'status': 'draft'
        }
        
        result = supabase.table('workflow_registry').insert(test_workflow).execute()
        if result.data:
            workflow_id = result.data[0]['id']
            print(f"✓ Successfully inserted test workflow: {workflow_id}")
            
            # Test 2: Query the workflow
            print("\n2. Testing workflow query...")
            query = supabase.table('workflow_registry').select("*").eq('id', workflow_id).execute()
            if query.data:
                print("✓ Successfully queried workflow")
                
            # Test 3: Update the workflow
            print("\n3. Testing workflow update...")
            update = supabase.table('workflow_registry').update({
                'status': 'testing'
            }).eq('id', workflow_id).execute()
            if update.data:
                print("✓ Successfully updated workflow")
                
            # Test 4: Clean up
            print("\n4. Cleaning up test data...")
            delete = supabase.table('workflow_registry').delete().eq('id', workflow_id).execute()
            print("✓ Test workflow deleted")
            
        print("\n✓ All operations successful - schema is working correctly!")
        
    except Exception as e:
        print(f"\n✗ Operation failed: {str(e)}")
        print("\nThis suggests schema issues. Please run the fix script.")

def main():
    """Main execution"""
    print("Workflow Registry Schema Verification Tool")
    print("=" * 60)
    
    # Check current schema
    check_schema()
    
    # Generate fix script
    generate_fix_script()
    
    # Test operations
    print("\nWould you like to test basic operations? (y/n): ", end='')
    if input().lower() == 'y':
        test_operations()
    
    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("\nNext steps:")
    print("1. Review any issues found above")
    print("2. If needed, run the fix script in sql/fix_workflow_schema.sql")
    print("3. Re-run this verification after fixes")

if __name__ == "__main__":
    main()