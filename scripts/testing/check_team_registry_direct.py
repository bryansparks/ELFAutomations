#!/usr/bin/env python3
"""
Check if team registry tables exist in Supabase using direct SQL
"""

import os
import sys

from dotenv import load_dotenv
from supabase import Client, create_client

# Team registry tables we're looking for
TEAM_REGISTRY_TABLES = ["teams", "team_members", "team_relationships", "team_audit_log"]


def check_team_registry_tables():
    """Check if team registry tables exist in Supabase."""
    print("🔍 Checking for Team Registry Tables in Supabase")
    print("=" * 50)

    # Load environment
    load_dotenv()

    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv(
        "SUPABASE_SERVICE_ROLE_KEY"
    )

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        print("Please ensure SUPABASE_URL and SUPABASE_ANON_KEY are set")
        return False

    print(f"✅ Using Supabase URL: {supabase_url}")

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        # Query for tables in public schema
        print("\n📊 Checking for team registry tables...")

        # Use RPC to query pg_tables
        query = """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename IN ('teams', 'team_members', 'team_relationships', 'team_audit_log')
        ORDER BY tablename;
        """

        # Execute raw SQL using postgrest
        response = supabase.postgrest.rpc("execute_sql", {"query": query}).execute()

        if response.data:
            existing_tables = [row["tablename"] for row in response.data]
        else:
            # Try alternative approach - check each table directly
            existing_tables = []
            for table in TEAM_REGISTRY_TABLES:
                try:
                    # Try to query the table
                    result = supabase.table(table).select("*").limit(0).execute()
                    existing_tables.append(table)
                except Exception:
                    # Table doesn't exist
                    pass

        print("\n📋 Team Registry Tables Status:")
        for table in TEAM_REGISTRY_TABLES:
            if table in existing_tables:
                print(f"  ✅ {table} - EXISTS")
            else:
                print(f"  ❌ {table} - NOT FOUND")

        if len(existing_tables) == len(TEAM_REGISTRY_TABLES):
            print("\n✅ All team registry tables exist!")

            # Get row counts
            print("\n📊 Getting row counts...")
            for table in existing_tables:
                try:
                    count_result = (
                        supabase.table(table).select("*", count="exact").execute()
                    )
                    count = count_result.count if hasattr(count_result, "count") else 0
                    print(f"  - {table}: {count} rows")
                except Exception as e:
                    print(f"  - {table}: Error getting count - {str(e)}")

            return True
        else:
            print(
                f"\n⚠️  Only {len(existing_tables)}/{len(TEAM_REGISTRY_TABLES)} tables exist"
            )
            return False

    except Exception as e:
        print(f"❌ Error checking tables: {str(e)}")

        # Try simpler approach - check each table individually
        print("\n🔄 Trying alternative approach...")
        existing_tables = []

        try:
            supabase: Client = create_client(supabase_url, supabase_key)

            for table in TEAM_REGISTRY_TABLES:
                try:
                    # Try to query the table
                    result = supabase.table(table).select("*").limit(0).execute()
                    existing_tables.append(table)
                    print(f"  ✅ {table} - EXISTS")
                except Exception:
                    print(f"  ❌ {table} - NOT FOUND")

            if existing_tables:
                print(f"\n📊 Found {len(existing_tables)} team registry tables")
                return len(existing_tables) == len(TEAM_REGISTRY_TABLES)
            else:
                print("\n❌ No team registry tables found")
                return False

        except Exception as e2:
            print(f"❌ Alternative approach also failed: {str(e2)}")
            return False


def main():
    """Main function."""
    success = check_team_registry_tables()

    if success:
        print("\n🎉 Team registry tables are already set up!")
    else:
        print("\n⚠️  Team registry tables need to be created")
        print("Run: python scripts/setup_team_registry.py")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
