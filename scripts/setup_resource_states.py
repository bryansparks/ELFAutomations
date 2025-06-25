#!/usr/bin/env python3
"""
Setup script for resource state management schema
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Create Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SECRET_KEY")

    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")

    return create_client(url, key)


def setup_resource_states():
    """Run the resource states SQL"""
    print("Setting up resource state management schema...")

    # Read SQL file
    sql_file = Path(__file__).parent.parent / "sql" / "create_resource_states.sql"
    with open(sql_file, "r") as f:
        sql_content = f.read()

    # Get Supabase client
    supabase = get_supabase_client()

    # Execute SQL
    try:
        # Note: This is a workaround - in production, use Supabase dashboard or migrations
        print("Please run the following SQL in your Supabase dashboard:")
        print(f"File: {sql_file}")
        print("\nAlternatively, you can use the Supabase CLI:")
        print(f"supabase db push --db-url $DATABASE_URL < {sql_file}")

        # For now, let's at least test the connection
        result = supabase.table("teams").select("count").execute()
        print(f"\nConnection successful! Found {result.data[0]['count']} teams.")

        print("\n✅ Next steps:")
        print("1. Run the SQL file in Supabase dashboard")
        print("2. The schema includes:")
        print("   - resource_states table for tracking current states")
        print("   - state_transitions table for history")
        print("   - mcp_registry table for MCP servers/clients")
        print("   - deployment_requirements table")
        print("   - Various views and functions")
        print("3. Start using the Control Center Resources page!")

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

    return True


def test_state_management():
    """Test the state management system"""
    print("\nTesting state management...")

    try:
        from elf_automations.shared.state_manager import WorkflowStateManager

        supabase = get_supabase_client()
        workflow_manager = WorkflowStateManager(supabase)

        print("✅ State manager modules loaded successfully!")

        # Show available transitions
        sm = workflow_manager.state_machine
        print(f"\nWorkflow states: {list(sm.states.keys())}")
        print(f"Initial state: {sm.initial_state}")
        print(
            f"Available transitions from 'created': {[t.to_state for t in sm.get_available_transitions()]}"
        )

    except ImportError as e:
        print(f"Import error: {str(e)}")
        print("Make sure you're running from the project root")
    except Exception as e:
        print(f"Error testing state management: {str(e)}")


if __name__ == "__main__":
    print("Resource State Management Setup")
    print("=" * 50)

    if setup_resource_states():
        test_state_management()
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)
