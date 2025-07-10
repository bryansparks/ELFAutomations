#!/usr/bin/env python3
"""
Check team registry using MCP server via subprocess.
This simulates how teams would actually use MCPs through AgentGateway.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def call_mcp_tool(tool_name, arguments):
    """Call an MCP tool via the TypeScript server"""
    # Build the MCP request
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": 1,
    }

    # Run the MCP server with the request
    cmd = [
        "node",
        str(
            Path(__file__).parent.parent
            / "mcp-servers-ts"
            / "src"
            / "supabase"
            / "server.js"
        ),
    ]

    # Note: This is a simplified version. In reality, MCPs communicate via stdio
    # For now, let's use a direct SQL check
    return None


def check_via_direct_sql():
    """Temporary direct check until MCP integration is clear"""
    try:
        from urllib.parse import urlparse

        import psycopg2

        # Get DB URL from environment
        db_url = os.getenv("SUPABASE_DB_URL")
        if not db_url:
            # Try to construct from .env
            import dotenv

            dotenv.load_dotenv(Path(__file__).parent.parent / ".env")

            # Check if we have the direct DB URL
            db_url = os.getenv("SUPABASE_DB_URL")
            if not db_url:
                print("❌ SUPABASE_DB_URL not found in environment")
                print("\nTo get your database URL:")
                print("1. Go to your Supabase project")
                print("2. Settings -> Database")
                print("3. Copy the 'Connection string' (URI)")
                print("4. Add to .env as SUPABASE_DB_URL=postgres://...")
                return False

        # Parse the URL
        parsed = urlparse(db_url)

        # Connect to database
        conn = psycopg2.connect(
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port,
        )

        cur = conn.cursor()

        # Check for tables
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('teams', 'team_members', 'team_relationships', 'team_audit_log')
            ORDER BY table_name;
        """
        )

        tables = cur.fetchall()

        if tables:
            print("✅ Found team registry tables:")
            for table in tables:
                print(f"   - {table[0]}")

            # Check team count
            cur.execute("SELECT COUNT(*) FROM teams;")
            count = cur.fetchone()[0]
            print(f"\n📊 Teams in registry: {count}")

            if count > 0:
                cur.execute(
                    "SELECT name, framework, department FROM teams ORDER BY created_at;"
                )
                teams = cur.fetchall()
                print("\n📋 Existing teams:")
                for team in teams:
                    dept = team[2] or "root"
                    print(f"   - {team[0]} ({team[1]}) in {dept}")

            conn.close()
            return True
        else:
            print("❌ Team registry tables not found")
            conn.close()
            return False

    except ImportError:
        print("❌ psycopg2 not installed")
        print("Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("🔍 Checking Team Registry status...\n")

    # For now, use direct SQL
    # TODO: Replace with proper MCP call when architecture is clear
    if check_via_direct_sql():
        print("\n✅ Team Registry is ready!")
        sys.exit(0)
    else:
        print("\n📝 Need to set up Team Registry")
        print("Run: python scripts/setup_team_registry.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
