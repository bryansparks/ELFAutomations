#!/usr/bin/env python3
"""
Simple team registry setup using Supabase REST API.
No MCP required - direct HTTP calls to Supabase.
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")  # Use service key for admin operations

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SECRET_KEY in .env")
    sys.exit(1)

# Team registry tables SQL
CREATE_TABLES_SQL = """
-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    framework VARCHAR(50) NOT NULL CHECK (framework IN ('crewai', 'langgraph')),
    department VARCHAR(255),
    manager_agent VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Team members table
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    agent_name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    capabilities TEXT[],
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    is_manager BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    UNIQUE(team_id, agent_name)
);

-- Team relationships table (who reports to whom)
CREATE TABLE IF NOT EXISTS team_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    child_team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'reports_to',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    UNIQUE(parent_team_id, child_team_id)
);

-- Audit log for team activities
CREATE TABLE IF NOT EXISTS team_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    performed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_teams_department ON teams(department);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_relationships_parent ON team_relationships(parent_team_id);
CREATE INDEX IF NOT EXISTS idx_team_relationships_child ON team_relationships(child_team_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_team_id ON team_audit_log(team_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON team_audit_log(created_at);
"""


def execute_sql(sql):
    """Execute SQL via Supabase REST API"""
    # Supabase doesn't expose direct SQL execution via REST API
    # We need to use the edge function or direct connection
    print("⚠️  Supabase REST API doesn't support direct SQL execution")
    print("📝 Let's create a different approach...")
    return False


def check_tables_exist():
    """Check if tables exist using REST API"""
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

    # Try to query the teams table
    response = requests.get(f"{SUPABASE_URL}/rest/v1/teams?limit=1", headers=headers)

    if response.status_code == 200:
        return True
    elif response.status_code == 404 or response.status_code == 400:
        return False
    else:
        print(f"❌ Unexpected response: {response.status_code}")
        print(response.text)
        return None


def main():
    print("🔍 Checking Team Registry status...\n")

    exists = check_tables_exist()

    if exists is True:
        print("✅ Team Registry tables already exist!")
        # Try to get count
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Prefer": "count=exact",
        }
        response = requests.get(f"{SUPABASE_URL}/rest/v1/teams", headers=headers)
        if response.status_code == 200:
            count = response.headers.get("content-range", "").split("/")[-1]
            print(f"📊 Teams in registry: {count}")
    elif exists is False:
        print("❌ Team Registry tables don't exist")
        print("\n📝 To create the tables, you need to:")
        print("1. Go to your Supabase project dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and run the SQL from scripts/sql/create_team_registry.sql")
        print("\nOr get the database connection string and run setup_team_registry.py")

        # Save SQL for easy access
        sql_path = Path(__file__).parent / "sql" / "create_team_registry.sql"
        sql_path.parent.mkdir(exist_ok=True)
        sql_path.write_text(CREATE_TABLES_SQL)
        print(f"\n💾 SQL saved to: {sql_path}")
    else:
        print("❓ Could not determine table status")
        print("Check your Supabase credentials")


if __name__ == "__main__":
    main()
