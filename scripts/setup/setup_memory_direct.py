#!/usr/bin/env python3
"""
Direct setup of Memory System tables in Supabase.

This follows the same proven pattern as setup_team_registry.py:
- Direct PostgreSQL connection
- No MCP needed for schema creation
- Simple and reliable
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_memory_tables():
    """Create memory system tables using direct PostgreSQL connection."""

    print("🚀 Setting up Memory System tables in Supabase")
    print("=" * 50)

    # Get database URL (same pattern as team registry)
    db_url = os.getenv("SUPABASE_DB_URL")

    if not db_url:
        # Build URL from components
        supabase_url = os.getenv("SUPABASE_URL", "")
        db_password = os.getenv("SUPABASE_PASSWORD", "")

        if not supabase_url or not db_password:
            print("❌ Missing SUPABASE_URL or SUPABASE_PASSWORD")
            print("\nOption 1: Set SUPABASE_DB_URL directly")
            print("Option 2: Set SUPABASE_URL and SUPABASE_PASSWORD")
            print("\nFind database password in Supabase dashboard:")
            print("Settings → Database → Connection string")
            return False

        # Extract project reference
        if "supabase.co" in supabase_url:
            project_ref = supabase_url.replace("https://", "").split(".supabase.co")[0]
            db_host = f"db.{project_ref}.supabase.co"

            # URL encode password for special characters
            encoded_password = quote_plus(db_password)
            db_url = f"postgresql://postgres:{encoded_password}@{db_host}:5432/postgres?sslmode=require"
        else:
            print("❌ Invalid SUPABASE_URL format")
            return False

    # Read SQL file
    sql_file = Path("sql/create_memory_system_tables.sql")
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return False

    with open(sql_file, "r") as f:
        sql_content = f.read()

    try:
        # Connect and execute
        print("📊 Connecting to database...")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        print("📊 Creating memory system tables...")
        cur.execute(sql_content)
        conn.commit()

        print("✅ Tables created successfully!")

        # Verify tables
        print("\n🔍 Verifying tables...")
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN (
                'memory_entries',
                'memory_collections',
                'learning_patterns',
                'memory_relationships',
                'team_knowledge_profiles',
                'memory_access_logs'
            )
            ORDER BY table_name;
        """
        )

        tables = cur.fetchall()
        print(f"✅ Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")

        # Create default collection
        print("\n📦 Creating default memory collection...")
        cur.execute(
            """
            INSERT INTO memory_collections (name, description, collection_type)
            VALUES ('default', 'Default memory collection for all teams', 'general')
            ON CONFLICT (name) DO NOTHING
            RETURNING name;
        """
        )
        conn.commit()

        result = cur.fetchone()
        if result:
            print("✅ Default collection created")
        else:
            print("ℹ️  Default collection already exists")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main entry point."""

    success = setup_memory_tables()

    if success:
        print("\n" + "=" * 50)
        print("🎉 Memory system tables created successfully!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Deploy Qdrant via GitOps:")
        print("   git add k8s/data-stores/qdrant/")
        print("   git commit -m 'feat: Add Qdrant vector database'")
        print("   git push")
        print("")
        print("2. After ArgoCD deploys Qdrant:")
        print("   - Build Memory & Learning MCP server")
        print("   - Create RAG free-agent team")
        print("   - Test with development mock")
    else:
        print("\n❌ Setup failed!")
        print("\nTroubleshooting:")
        print("1. Check SUPABASE_URL and SUPABASE_PASSWORD in .env")
        print("2. Or set SUPABASE_DB_URL directly")
        print("3. Verify database password in Supabase dashboard")


if __name__ == "__main__":
    main()
