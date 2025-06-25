#!/usr/bin/env python3
"""
Verify RAG Schema in Supabase
Checks if the RAG extraction tables have been created
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.utils import get_supabase_client


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

            # Show the SQL file location
            sql_file = (
                Path(__file__).parent.parent
                / "sql"
                / "create_rag_extraction_tables.sql"
            )
            if sql_file.exists():
                print(f"\nSQL file location: {sql_file}")
            else:
                print("\n⚠️  SQL file not found at expected location!")

    except Exception as e:
        print(f"\n❌ Error connecting to Supabase: {str(e)}")
        print("\nMake sure environment variables are set:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_ANON_KEY or SUPABASE_KEY")


if __name__ == "__main__":
    verify_rag_schema()
