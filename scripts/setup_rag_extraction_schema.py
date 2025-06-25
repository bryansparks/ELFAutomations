#!/usr/bin/env python3
"""
Setup script for RAG extraction schema extensions.
Run this after the base RAG schema is created.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Simple configuration loading
def get_supabase_client():
    """Get Supabase client with proper configuration."""
    from supabase import Client, create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables!")
        print("Please ensure your .env file is configured properly.")
        sys.exit(1)

    return create_client(url, key)


def run_sql_file(supabase_client, sql_file_path):
    """Execute SQL file contents."""
    with open(sql_file_path, "r") as f:
        sql_content = f.read()

    # Split by semicolons but be careful with functions
    statements = []
    current_statement = []
    in_function = False

    for line in sql_content.split("\n"):
        if "CREATE OR REPLACE FUNCTION" in line:
            in_function = True
        elif "$$ LANGUAGE plpgsql;" in line:
            in_function = False
            current_statement.append(line)
            statements.append("\n".join(current_statement))
            current_statement = []
            continue

        current_statement.append(line)

        if not in_function and line.strip().endswith(";"):
            statements.append("\n".join(current_statement))
            current_statement = []

    # Execute each statement
    for statement in statements:
        statement = statement.strip()
        if not statement or statement.startswith("--"):
            continue

        try:
            # Use RPC to execute raw SQL
            result = supabase_client.rpc("exec_sql", {"query": statement}).execute()
            print(f"✓ Executed: {statement[:50]}...")
        except Exception as e:
            if "already exists" in str(e):
                print(f"⚠️  Already exists: {statement[:50]}...")
            else:
                print(f"❌ Error executing: {statement[:50]}...")
                print(f"   Error: {str(e)}")
                return False

    return True


def main():
    """Main setup function."""
    print("🚀 Setting up RAG Extraction Schema Extensions")
    print("=" * 50)

    try:
        # Get Supabase client
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")

        # Run extraction schema SQL
        sql_file = (
            Path(__file__).parent.parent / "sql" / "create_rag_extraction_tables.sql"
        )

        if not sql_file.exists():
            print(f"❌ SQL file not found: {sql_file}")
            return 1

        print(f"\n📝 Running extraction schema from: {sql_file}")

        if run_sql_file(supabase, sql_file):
            print("\n✅ Extraction schema created successfully!")

            # Verify some key tables
            print("\n🔍 Verifying tables...")
            tables_to_check = [
                "rag_extraction_schemas",
                "rag_extracted_entities",
                "rag_entity_relationships",
                "rag_chunk_relationships",
                "rag_document_classifications",
            ]

            for table in tables_to_check:
                try:
                    result = supabase.table(table).select("*").limit(1).execute()
                    print(f"✅ Table {table} is accessible")
                except Exception as e:
                    print(f"❌ Table {table} not accessible: {str(e)}")

            # Check if default schemas were inserted
            try:
                schemas = supabase.table("rag_extraction_schemas").select("*").execute()
                if schemas.data:
                    print(f"\n✅ Found {len(schemas.data)} default extraction schemas:")
                    for schema in schemas.data:
                        print(
                            f"   - {schema['document_type']}: {schema['display_name']}"
                        )
            except Exception as e:
                print(f"⚠️  Could not verify extraction schemas: {str(e)}")

            print("\n🎉 RAG extraction schema setup complete!")
            print("\nNext steps:")
            print("1. Create the RAG processor team")
            print("2. Implement document processing pipeline")
            print("3. Test with sample documents")

            return 0
        else:
            print("\n❌ Some errors occurred during setup")
            return 1

    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    sys.exit(main())
