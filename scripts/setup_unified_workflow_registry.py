#!/usr/bin/env python3
"""
Setup script for the unified workflow registry

This script:
1. Creates the new unified workflow registry schema
2. Migrates existing data from old schemas
3. Provides options for testing or production deployment
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_db_connection():
    """Get PostgreSQL connection from Supabase URL"""
    database_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

    if not database_url:
        print("❌ Error: DATABASE_URL or SUPABASE_DB_URL not set in .env file")
        sys.exit(1)

    return psycopg2.connect(database_url)


def execute_sql_file(conn, sql_file: Path, description: str):
    """Execute a SQL file"""
    print(f"\n📋 {description}...")

    try:
        with open(sql_file, "r") as f:
            sql_content = f.read()

        with conn.cursor() as cursor:
            cursor.execute(sql_content)

        conn.commit()
        print(f"✅ {description} completed successfully")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error during {description}: {e}")
        raise


def main():
    """Main setup function"""
    print("🚀 Setting up Unified Workflow Registry")
    print("=" * 50)

    # Get SQL directory
    sql_dir = Path(__file__).parent.parent / "sql"

    # Check if SQL files exist
    schema_file = sql_dir / "create_unified_workflow_registry.sql"
    migration_file = sql_dir / "migrate_to_unified_workflow_registry.sql"

    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        sys.exit(1)

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    # Prompt for confirmation
    print("\nThis script will:")
    print("1. Create the new unified workflow registry schema")
    print("2. Migrate data from existing workflow tables")
    print("3. Create indexes and views for performance")
    print("\n⚠️  WARNING: This will modify your database schema!")

    response = input("\nDo you want to continue? (yes/no): ").lower()
    if response != "yes":
        print("❌ Setup cancelled")
        sys.exit(0)

    # Ask about migration
    migrate_data = (
        input("\nMigrate existing workflow data? (yes/no): ").lower() == "yes"
    )

    try:
        # Connect to database
        print("\n🔌 Connecting to database...")
        conn = get_db_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("✅ Connected to database")

        # Create schema
        execute_sql_file(conn, schema_file, "Creating unified workflow registry schema")

        # Run migration if requested
        if migrate_data:
            execute_sql_file(conn, migration_file, "Migrating existing workflow data")
        else:
            print("\n⏭️  Skipping data migration")

        # Verify setup
        print("\n🔍 Verifying setup...")
        with conn.cursor() as cursor:
            # Check tables
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN (
                    'workflow_registry',
                    'workflow_versions',
                    'workflow_executions',
                    'workflow_templates',
                    'workflow_validation_log',
                    'workflow_import_export_log'
                )
                ORDER BY table_name
            """
            )

            tables = cursor.fetchall()
            print(f"\n📊 Created {len(tables)} tables:")
            for table in tables:
                print(f"   ✓ {table[0]}")

            # Check workflow count
            cursor.execute("SELECT COUNT(*) FROM workflow_registry")
            workflow_count = cursor.fetchone()[0]
            print(f"\n📈 Total workflows in registry: {workflow_count}")

            if workflow_count > 0:
                # Show some stats
                cursor.execute(
                    """
                    SELECT status, COUNT(*)
                    FROM workflow_registry
                    GROUP BY status
                    ORDER BY COUNT(*) DESC
                """
                )
                print("\n📊 Workflows by status:")
                for status, count in cursor.fetchall():
                    print(f"   - {status}: {count}")

        print("\n✅ Setup completed successfully!")

        # Print next steps
        print("\n📝 Next Steps:")
        print("1. Use the workflow manager CLI to import workflows:")
        print(
            "   python scripts/n8n_workflow_manager.py import <workflow.json> --category <category> --team <team>"
        )
        print("\n2. Validate imported workflows:")
        print(
            "   python scripts/n8n_workflow_manager.py validate <workflow-name> --deep"
        )
        print("\n3. Export workflows for backup:")
        print(
            "   python scripts/n8n_workflow_manager.py export <workflow-name> --output backup.json"
        )
        print("\n4. Sync with N8N instance:")
        print("   python scripts/n8n_workflow_manager.py sync --all")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
