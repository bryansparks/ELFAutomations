#!/usr/bin/env python3
"""
Setup Team Registry in Supabase
This creates the tables and functions needed for tracking teams and their relationships
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.supabase_client import get_supabase_client


def setup_team_registry():
    """Create Team Registry schema in Supabase"""
    print("🚀 Setting up Team Registry in Supabase...")
    
    # Get Supabase client
    client = get_supabase_client()
    
    # Read SQL file
    sql_file = Path(__file__).parent.parent / "sql" / "create_team_registry.sql"
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    try:
        # Execute SQL
        # Note: Supabase Python client doesn't have direct SQL execution
        # We need to use the REST API or connect via psycopg2
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse Supabase URL to get connection details
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        # For Supabase, we need the direct database URL
        # This is typically provided as SUPABASE_DB_URL or similar
        db_url = os.getenv('SUPABASE_DB_URL')
        
        if not db_url:
            print("❌ SUPABASE_DB_URL environment variable not set")
            print("Please set it to your Supabase PostgreSQL connection string")
            print("You can find this in your Supabase project settings under 'Database'")
            return False
        
        # Connect and execute
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Execute the SQL
        cur.execute(sql_content)
        conn.commit()
        
        print("✅ Team Registry schema created successfully!")
        
        # Verify tables were created
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('teams', 'team_members', 'team_relationships', 
                              'executive_management', 'team_communication_patterns', 
                              'team_audit_log')
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Close connection
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Team Registry: {e}")
        return False


def verify_registry():
    """Verify the Team Registry is properly set up"""
    client = get_supabase_client()
    
    try:
        # Test by querying the teams table
        result = client.table('teams').select("*").execute()
        print(f"\n✅ Team Registry verified - teams table has {len(result.data)} teams")
        
        # Check if executive-team exists
        exec_team = client.table('teams').select("*").eq('name', 'executive-team').execute()
        if exec_team.data:
            print("   - Executive team already registered")
        else:
            print("   - Executive team not yet registered")
        
        return True
    except Exception as e:
        print(f"❌ Error verifying registry: {e}")
        return False


def register_executive_team():
    """Register the existing executive team in the registry"""
    client = get_supabase_client()
    
    try:
        # Check if already exists
        existing = client.table('teams').select("*").eq('name', 'executive-team').execute()
        if existing.data:
            print("ℹ️  Executive team already registered")
            return True
        
        # Register executive team
        team_data = {
            'name': 'executive-team',
            'display_name': 'Executive Leadership Team',
            'department': 'executive',
            'placement': 'executive',
            'purpose': 'Provide strategic leadership and coordinate all company operations',
            'framework': 'CrewAI',
            'llm_provider': 'OpenAI',
            'llm_model': 'gpt-4',
            'status': 'active'
        }
        
        result = client.table('teams').insert(team_data).execute()
        team_id = result.data[0]['id']
        
        # Add team members
        executives = [
            {'role': 'Chief Executive Officer', 'is_manager': True},
            {'role': 'Chief Technology Officer', 'is_manager': False},
            {'role': 'Chief Marketing Officer', 'is_manager': False},
            {'role': 'Chief Operations Officer', 'is_manager': False},
            {'role': 'Chief Financial Officer', 'is_manager': False}
        ]
        
        for exec in executives:
            member_data = {
                'team_id': team_id,
                'role': exec['role'],
                'is_manager': exec['is_manager'],
                'responsibilities': ['Lead company strategy', 'Manage departments'],
                'skills': ['Leadership', 'Strategic thinking']
            }
            client.table('team_members').insert(member_data).execute()
        
        print("✅ Executive team registered successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error registering executive team: {e}")
        return False


if __name__ == "__main__":
    # Setup registry
    if setup_team_registry():
        # Verify it works
        if verify_registry():
            # Register executive team
            register_executive_team()
            
            print("\n🎉 Team Registry is ready!")
            print("Next steps:")
            print("1. Update team-factory.py to register teams")
            print("2. Test creating a new team")
            print("3. Verify relationships are tracked")
    else:
        print("\n❌ Failed to setup Team Registry")
        print("Please check your Supabase connection settings")