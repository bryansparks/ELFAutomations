#!/usr/bin/env python3
"""
Setup team chat interface tables in Supabase.
This adds chat support to the existing team registry.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "elf_automations"))

from elf_automations.shared.database.supabase_executor import SupabaseExecutor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_team_chat_tables():
    """Create team chat tables and update team registry."""
    # Load environment variables
    load_dotenv()

    # Initialize Supabase executor
    executor = SupabaseExecutor()

    try:
        # Read the SQL file
        sql_file = Path(__file__).parent.parent / "sql" / "add_team_chat_tables.sql"
        logger.info(f"Reading SQL from {sql_file}")

        with open(sql_file, "r") as f:
            sql_content = f.read()

        # Execute the SQL
        logger.info("Creating team chat tables...")
        executor.execute(sql_content)

        # Verify the tables were created
        logger.info("Verifying table creation...")

        # Check teams table has new columns
        teams_check = executor.query(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'teams'
            AND column_name IN ('is_top_level', 'enable_chat_interface', 'chat_config')
            ORDER BY column_name;
        """
        )

        if teams_check and len(teams_check) == 3:
            logger.info("✓ Teams table updated with chat columns")
        else:
            logger.error("✗ Teams table missing chat columns")
            return False

        # Check new tables
        tables_to_check = [
            "team_chat_sessions",
            "team_chat_messages",
            "team_chat_delegations",
        ]

        for table in tables_to_check:
            result = executor.query(
                f"""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = '{table}';
            """
            )

            if result and result[0]["count"] > 0:
                logger.info(f"✓ Table '{table}' created successfully")
            else:
                logger.error(f"✗ Table '{table}' not found")
                return False

        # Check views
        views_to_check = ["active_chat_sessions", "team_chat_statistics"]

        for view in views_to_check:
            result = executor.query(
                f"""
                SELECT COUNT(*) as count
                FROM information_schema.views
                WHERE table_schema = 'public'
                AND table_name = '{view}';
            """
            )

            if result and result[0]["count"] > 0:
                logger.info(f"✓ View '{view}' created successfully")
            else:
                logger.error(f"✗ View '{view}' not found")
                return False

        # Update executive team to be top-level with chat enabled
        logger.info("Updating executive team for chat support...")

        executor.execute(
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
            RETURNING id, name;
        """
        )

        update_result = executor.query(
            "SELECT id, name FROM teams WHERE name = 'executive-team' AND enable_chat_interface = true;"
        )

        if update_result:
            logger.info(f"✓ Updated {len(update_result)} team(s) for chat support")

        # Also update any existing department heads
        dept_heads = [
            "engineering-team",
            "marketing-team",
            "operations-team",
            "finance-team",
        ]
        for team_name in dept_heads:
            executor.execute(
                f"""
                UPDATE teams
                SET
                    is_top_level = true,
                    enable_chat_interface = true,
                    chat_config = jsonb_build_object(
                        'allowed_roles', ARRAY['admin', 'user'],
                        'max_session_duration_minutes', 45,
                        'max_messages_per_session', 50,
                        'enable_delegation_preview', true
                    )
                WHERE name = '{team_name}';
            """
            )

        logger.info("✅ Team chat tables setup completed successfully!")

        # Show summary
        summary = executor.query(
            """
            SELECT
                COUNT(*) FILTER (WHERE is_top_level = true) as top_level_teams,
                COUNT(*) FILTER (WHERE enable_chat_interface = true) as chat_enabled_teams,
                COUNT(*) as total_teams
            FROM teams;
        """
        )

        if summary:
            stats = summary[0]
            logger.info(f"\nTeam Statistics:")
            logger.info(f"  Total teams: {stats['total_teams']}")
            logger.info(f"  Top-level teams: {stats['top_level_teams']}")
            logger.info(f"  Chat-enabled teams: {stats['chat_enabled_teams']}")

        return True

    except Exception as e:
        logger.error(f"Error setting up team chat tables: {e}")
        return False


if __name__ == "__main__":
    success = setup_team_chat_tables()
    sys.exit(0 if success else 1)
