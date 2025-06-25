#!/usr/bin/env python3
"""
Simple RAG Schema Verification
Checks if the RAG extraction tables have been created
"""

import os

from supabase import Client, create_client


def get_supabase_client() -> Client:
    """Get Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

    return create_client(url, key)


def verify_rag_schema():
    """Verify RAG schema exists in Supabase"""
    print("🔍 Verifying RAG Schema in Supabase...")
    print("=" * 50)

    try:
        supabase = get_supabase_client()

        # Tables to check
        tables_to_check = [
            "rag_extraction_schemas",
            "rag_extracted_entities",
            "rag_entity_relationships",
            "rag_document_classifications",
            "rag_extraction_history",
            "rag_chunk_relationships",
        ]

        print("\nChecking tables:")
        all_exist = True

        for table in tables_to_check:
            try:
                # Try to query the table (limit 1 to be fast)
                result = supabase.table(table).select("*").limit(1).execute()
                print(f"✅ {table} - EXISTS")
            except Exception as e:
                print(f"❌ {table} - NOT FOUND")
                all_exist = False

        if all_exist:
            print("\n✅ All RAG extraction tables exist!")

            # Check if default schemas are loaded
            print("\nChecking default extraction schemas:")
            schemas = (
                supabase.table("rag_extraction_schemas")
                .select("document_type")
                .execute()
            )

            if schemas.data:
                print("Found schemas for:")
                for schema in schemas.data:
                    print(f"  - {schema['document_type']}")
            else:
                print(
                    "⚠️  No extraction schemas found. Run the SQL script to add defaults."
                )

        else:
            print("\n❌ Some tables are missing!")
            print("\nTo create the schema:")
            print("1. Go to Supabase Dashboard > SQL Editor")
            print("2. Create a new query")
            print("3. Copy contents from: sql/create_rag_extraction_tables.sql")
            print("4. Run the query")

            sql_file = "/Users/bryansparks/projects/ELFAutomations/sql/create_rag_extraction_tables.sql"
            print(f"\nSQL file location: {sql_file}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure environment variables are set:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_ANON_KEY or SUPABASE_KEY")


if __name__ == "__main__":
    verify_rag_schema()
