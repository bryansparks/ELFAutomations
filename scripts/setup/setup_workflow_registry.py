#!/usr/bin/env python3
"""
Setup Workflow Registry in Supabase for n8n integration
Tracks configured workflows and their execution history
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Create Supabase client from environment variables"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)

    return create_client(url, key)


def setup_workflow_registry():
    """Set up the workflow registry schema in Supabase"""
    print("Setting up Workflow Registry in Supabase...")

    # Get SQL file path
    sql_file = Path(__file__).parent.parent / "sql" / "create_workflow_registry.sql"

    if not sql_file.exists():
        print(f"Error: SQL file not found at {sql_file}")
        sys.exit(1)

    # Read SQL content
    with open(sql_file, "r") as f:
        sql_content = f.read()

    # Connect to Supabase
    supabase = get_supabase_client()

    try:
        # Execute SQL
        # Note: Supabase Python client doesn't directly support raw SQL execution
        # You'll need to run this SQL directly in Supabase SQL editor or via psql
        print("\nPlease execute the following SQL in Supabase SQL editor:")
        print(f"\nSQL file location: {sql_file}")
        print("\nOr run via psql:")
        print(f"psql $SUPABASE_DB_URL < {sql_file}")

        # Test connection by checking if we can query
        print("\nTesting Supabase connection...")
        result = supabase.table("workflow_registry").select("*").limit(1).execute()
        print("✓ Workflow registry table already exists!")

        # Show sample data
        workflows = supabase.table("workflow_registry").select("*").execute()
        if workflows.data:
            print(f"\nFound {len(workflows.data)} workflows:")
            for wf in workflows.data:
                print(f"  - {wf['n8n_workflow_name']} ({wf['status']})")

    except Exception as e:
        if "workflow_registry" in str(e):
            print("\n✗ Workflow registry table does not exist yet.")
            print("Please run the SQL script first.")
        else:
            print(f"\nError: {e}")

    # Provide Python helper functions
    print("\n" + "=" * 60)
    print("Python Helper Functions for Workflow Registry:")
    print("=" * 60)

    print(
        """
# Register a new workflow
from supabase import create_client
import os

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Register workflow
workflow = supabase.rpc('register_workflow', {
    'p_n8n_workflow_id': 'abc-123',
    'p_n8n_workflow_name': 'Customer Onboarding',
    'p_description': 'Automated customer onboarding process',
    'p_category': 'customer_onboarding',
    'p_owner_team': 'sales-team',
    'p_webhook_url': 'http://n8n.elf-automations.local/webhook/customer-onboard'
}).execute()

# Approve workflow
supabase.rpc('approve_workflow', {
    'p_workflow_id': workflow.data,
    'p_approved_by': 'admin',
    'p_notes': 'Tested and approved for production'
}).execute()

# Activate workflow
supabase.rpc('activate_workflow', {
    'p_workflow_id': workflow.data
}).execute()

# Record execution
supabase.rpc('record_workflow_execution', {
    'p_workflow_id': workflow.data,
    'p_execution_id': 'exec-456',
    'p_triggered_by': 'sales-team',
    'p_status': 'success',
    'p_duration_ms': 1234,
    'p_input_data': {'customer_id': '789'},
    'p_output_data': {'welcome_email_sent': True}
}).execute()
"""
    )


def test_workflow_operations():
    """Test basic workflow operations"""
    print("\n" + "=" * 60)
    print("Testing Workflow Operations:")
    print("=" * 60)

    supabase = get_supabase_client()

    try:
        # Test registering a workflow
        print("\n1. Registering test workflow...")
        result = supabase.rpc(
            "register_workflow",
            {
                "p_n8n_workflow_id": "test-python-001",
                "p_n8n_workflow_name": "Python Test Workflow",
                "p_description": "Test workflow created from Python",
                "p_category": "other",
                "p_owner_team": "n8n-interface-team",
            },
        ).execute()

        if result.data:
            workflow_id = result.data
            print(f"✓ Workflow registered with ID: {workflow_id}")

            # Get workflow details
            workflow = (
                supabase.table("workflow_registry")
                .select("*")
                .eq("id", workflow_id)
                .single()
                .execute()
            )
            print(f"  Status: {workflow.data['status']}")
            print(f"  Owner: {workflow.data['owner_team']}")

    except Exception as e:
        print(f"Note: {e}")
        print("This is expected if the schema hasn't been created yet.")


if __name__ == "__main__":
    setup_workflow_registry()
    # test_workflow_operations()  # Uncomment after schema is created
