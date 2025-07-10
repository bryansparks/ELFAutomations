#!/usr/bin/env python3
"""
Simple setup script for team chat tables - uses environment variables directly
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from supabase import Client, create_client
except ImportError:
    print("Error: supabase package not installed")
    print("Run: pip install supabase")
    sys.exit(1)


def main():
    """Setup team chat tables"""
    # Get credentials from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY/SUPABASE_ANON_KEY")
        print("Please check your .env file")
        return False

    print(f"Connecting to Supabase at {supabase_url[:30]}...")

    # For direct SQL execution, we need psycopg2
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        print("Error: psycopg2 not installed")
        print("Run: pip install psycopg2-binary")
        return False

    # Get database connection string
    db_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")

    if not db_url:
        print("\nError: No direct database URL found")
        print("Please set SUPABASE_DB_URL or DATABASE_URL in your .env file")
        print(
            "Format: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
        )
        return False

    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Read SQL file
        sql_file = Path(__file__).parent.parent / "sql" / "add_team_chat_tables.sql"
        print(f"Reading SQL from {sql_file}")

        with open(sql_file, "r") as f:
            sql_content = f.read()

        # Execute SQL
        print("Creating team chat tables...")
        cursor.execute(sql_content)
        conn.commit()

        # Verify tables
        print("\nVerifying table creation...")

        # Check teams columns
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'teams'
            AND column_name IN ('is_top_level', 'enable_chat_interface', 'chat_config')
            ORDER BY column_name;
        """
        )
        columns = cursor.fetchall()

        if len(columns) == 3:
            print("✓ Teams table updated with chat columns")
        else:
            print(f"✗ Expected 3 columns, found {len(columns)}")

        # Check new tables
        tables = ["team_chat_sessions", "team_chat_messages", "team_chat_delegations"]
        for table in tables:
            cursor.execute(
                f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                );
            """
            )
            exists = cursor.fetchone()["exists"]
            if exists:
                print(f"✓ Table '{table}' created")
            else:
                print(f"✗ Table '{table}' missing")

        # Update teams
        print("\nUpdating teams for chat support...")

        # Update executive team
        cursor.execute(
            """
            UPDATE teams
            SET
                is_top_level = true,
                enable_chat_interface = true,
                chat_config = jsonb_build_object(
                    'allowed_roles', ARRAY['admin', 'user'],
                    'max_session_duration_minutes', 60,
                    'max_messages_per_session', 100,
                    'enable_delegation_preview', true
                )
            WHERE name = 'executive-team'
            RETURNING name;
        """
        )
        updated = cursor.fetchall()
        if updated:
            print(f"✓ Updated executive-team")

        # Get summary
        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE is_top_level = true) as top_level_teams,
                COUNT(*) FILTER (WHERE enable_chat_interface = true) as chat_enabled_teams,
                COUNT(*) as total_teams
            FROM teams;
        """
        )
        stats = cursor.fetchone()

        print(f"\nTeam Statistics:")
        print(f"  Total teams: {stats['total_teams']}")
        print(f"  Top-level teams: {stats['top_level_teams']}")
        print(f"  Chat-enabled teams: {stats['chat_enabled_teams']}")

        conn.commit()
        cursor.close()
        conn.close()

        print("\n✅ Team chat tables setup completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
