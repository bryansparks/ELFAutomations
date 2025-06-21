#!/usr/bin/env python3
"""
Simple N8N Registry Setup - Just outputs the SQL to run

This script outputs the complete SQL that needs to be run in Supabase.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def main():
    """Output the SQL for N8N registry setup"""

    # Test Supabase connection
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_SECRET_KEY")
    )

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        sys.exit(1)

    print("✓ Supabase credentials found\n")

    # Read SQL file
    sql_file = Path(__file__).parent.parent / "sql" / "create_n8n_workflow_registry.sql"

    print("=" * 80)
    print("N8N WORKFLOW REGISTRY SETUP")
    print("=" * 80)
    print("\nCopy and run the following SQL in your Supabase SQL Editor:")
    print(f"Navigate to: https://app.supabase.com/project/[your-project]/sql/new")
    print("\n" + "-" * 80 + "\n")

    with open(sql_file, "r") as f:
        print(f.read())

    print("\n" + "-" * 80)
    print("\nAfter running the SQL, verify with:")
    print("  python scripts/setup_n8n_registry.py --verify")

    # Test connection
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        # Try a simple query to test connection
        result = supabase.table("team_registry").select("count").execute()
        print("\n✓ Successfully connected to Supabase")
    except Exception as e:
        print(f"\n! Warning: Could not connect to Supabase: {e}")


if __name__ == "__main__":
    main()
