#!/usr/bin/env python3
"""
Verify RAG extraction tables exist in Supabase.
Run this after manually applying create_rag_extraction_tables.sql in Supabase Dashboard.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from supabase import create_client


def main():
    """Verify extraction tables exist."""
    print("🔍 Verifying RAG Extraction Tables")
    print("=" * 50)

    # Get Supabase client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY!")
        return 1

    supabase = create_client(url, key)
    print("✅ Connected to Supabase")

    # Tables to verify
    tables = [
        "rag_extraction_schemas",
        "rag_extracted_entities",
        "rag_entity_relationships",
        "rag_chunk_relationships",
        "rag_document_classifications",
        "rag_extraction_history",
    ]

    print("\n📋 Checking tables...")
    all_good = True

    for table in tables:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            print(f"✅ {table} exists")
        except Exception as e:
            print(f"❌ {table} not found: {str(e)}")
            all_good = False

    # Check extraction schemas
    if all_good:
        try:
            schemas = supabase.table("rag_extraction_schemas").select("*").execute()
            if schemas.data:
                print(f"\n📄 Found {len(schemas.data)} extraction schemas:")
                for schema in schemas.data:
                    print(f"   • {schema['document_type']}: {schema['display_name']}")
                    entity_types = schema.get("entity_types", [])
                    print(f"     Entity types: {', '.join(entity_types)}")
            else:
                print(
                    "\n⚠️  No extraction schemas found. You may need to run the INSERT statements."
                )
        except Exception as e:
            print(f"\n❌ Could not query extraction schemas: {str(e)}")

    if all_good:
        print("\n✅ All extraction tables verified!")
        print("\n📝 Next step: Run the SQL INSERT statements to add default schemas")
        print("   Copy the INSERT statements from create_rag_extraction_tables.sql")
        print("   and run them in the Supabase SQL Editor")
    else:
        print("\n❌ Some tables are missing!")
        print("\n📝 Please run the following in Supabase SQL Editor:")
        print("   1. Go to your Supabase dashboard")
        print("   2. Navigate to SQL Editor")
        print("   3. Copy contents of sql/create_rag_extraction_tables.sql")
        print("   4. Run the SQL")

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
