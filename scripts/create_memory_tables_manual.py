#!/usr/bin/env python3
"""
Manual creation instructions for Memory System tables in Supabase.

Since direct SQL execution is having issues, this script provides:
1. Instructions for manual creation via Supabase dashboard
2. Verification using Supabase client
"""

import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_manual_instructions():
    """Print instructions for manual table creation."""
    
    sql_file = Path("sql/create_memory_system_tables.sql")
    
    print("=" * 70)
    print("📋 MANUAL TABLE CREATION INSTRUCTIONS")
    print("=" * 70)
    print()
    print("Since direct database connection is having issues, please create")
    print("the tables manually using the Supabase dashboard:")
    print()
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to: SQL Editor (left sidebar)")
    print("3. Click 'New Query'")
    print("4. Copy the contents of:")
    print(f"   {sql_file.absolute()}")
    print("5. Paste into the SQL editor")
    print("6. Click 'Run' (or press Cmd/Ctrl + Enter)")
    print()
    print("The SQL file creates these tables:")
    print("  - memory_entries         (core memory storage)")
    print("  - memory_collections     (organize memories)")
    print("  - learning_patterns      (extracted insights)")
    print("  - memory_relationships   (connect memories)")
    print("  - team_knowledge_profiles (team expertise)")
    print("  - memory_access_logs     (usage tracking)")
    print()
    print("Plus views, functions, and indexes for performance.")
    print()
    print("=" * 70)
    

def verify_tables():
    """Verify tables exist using Supabase client."""
    
    print("\n🔍 Verifying table creation...")
    
    try:
        # Create Supabase client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment")
            return False
        
        supabase = create_client(url, key)
        
        # Test each table
        tables = [
            "memory_entries",
            "memory_collections", 
            "learning_patterns",
            "memory_relationships",
            "team_knowledge_profiles",
            "memory_access_logs"
        ]
        
        tables_found = []
        tables_missing = []
        
        for table in tables:
            try:
                # Try to query the table (limit 0 just to check it exists)
                result = supabase.table(table).select("*").limit(0).execute()
                tables_found.append(table)
                print(f"✅ Table '{table}' exists")
            except Exception as e:
                tables_missing.append(table)
                print(f"❌ Table '{table}' not found")
        
        print()
        if tables_missing:
            print(f"⚠️  Missing {len(tables_missing)} tables: {', '.join(tables_missing)}")
            print("Please create them using the instructions above.")
            return False
        else:
            print("🎉 All memory system tables exist!")
            
            # Try to create default collection
            print("\n📦 Creating default memory collection...")
            try:
                result = supabase.table("memory_collections").insert({
                    "name": "default",
                    "description": "Default memory collection for all teams",
                    "collection_type": "general"
                }).execute()
                print("✅ Default collection created")
            except Exception as e:
                if "duplicate key" in str(e):
                    print("ℹ️  Default collection already exists")
                else:
                    print(f"⚠️  Could not create default collection: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False


def print_next_steps():
    """Print next steps after table creation."""
    
    print("\n" + "="*70)
    print("📝 NEXT STEPS")
    print("="*70)
    print()
    print("1. Deploy Qdrant to K3s:")
    print("   git add k8s/data-stores/qdrant/")
    print("   git commit -m 'feat: Add Qdrant vector database'")
    print("   git push")
    print()
    print("2. For local development:")
    print("   - Use MockQdrantClient (see docs/MEMORY_SYSTEM_DEVELOPMENT_GUIDE.md)")
    print("   - Set USE_MOCK_QDRANT=true")
    print()
    print("3. Build Memory & Learning MCP:")
    print("   - Location: mcp-servers-ts/src/memory-learning/")
    print("   - Use mock Qdrant for local testing")
    print()
    print("4. Create RAG team:")
    print("   python tools/team_factory.py")
    print("   - Type: 'knowledge'")
    print("   - Department: 'free-agent'")
    print()


def main():
    """Main entry point."""
    
    print("🚀 Memory System Table Setup")
    print()
    
    # First, print manual instructions
    print_manual_instructions()
    
    # Ask user if they've created tables
    print()
    response = input("Have you created the tables in Supabase? (y/n): ").lower()
    
    if response == 'y':
        # Verify tables exist
        if verify_tables():
            print_next_steps()
        else:
            print("\n⚠️  Please complete table creation in Supabase dashboard first.")
    else:
        print("\n👉 Please follow the instructions above to create the tables.")
        print("   Then run this script again to verify.")


if __name__ == "__main__":
    main()