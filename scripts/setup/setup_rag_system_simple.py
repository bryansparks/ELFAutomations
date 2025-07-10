#!/usr/bin/env python3
"""
Simple setup script for the Multi-Tenant RAG System database schema.

This version avoids complex imports and uses direct Supabase connection.
"""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from supabase import Client, create_client

console = Console()


def get_supabase_client() -> Client:
    """Get Supabase client with error handling."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        console.print(
            "[red]Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set![/red]"
        )
        console.print("\nExample:")
        console.print("export SUPABASE_URL='https://your-project.supabase.co'")
        console.print("export SUPABASE_KEY='your-anon-or-service-key'")
        sys.exit(1)

    return create_client(url, key)


def run_sql_file(client: Client, sql_file: Path) -> bool:
    """Execute SQL file content."""
    try:
        with open(sql_file, "r") as f:
            sql_content = f.read()

        # Split into individual statements (simple split by semicolon)
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]

        console.print(f"[yellow]Executing {len(statements)} SQL statements...[/yellow]")

        # Note: Supabase Python client doesn't have direct SQL execution
        # You'll need to run this SQL directly in Supabase dashboard or use psql

        console.print(
            "\n[yellow]Important: The SQL schema needs to be executed directly in Supabase.[/yellow]"
        )
        console.print("\nOptions:")
        console.print("1. Copy the contents of sql/create_rag_system_tables.sql")
        console.print("2. Go to your Supabase dashboard > SQL Editor")
        console.print("3. Paste and run the SQL")
        console.print("\nOr use psql with your database connection string")

        return True

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


def verify_schema(client: Client) -> bool:
    """Verify the RAG schema was created."""
    console.print("\n[yellow]Verifying schema...[/yellow]")

    try:
        # Try to query the tenants table in rag schema
        result = client.from_("rag.tenants").select("*", count="exact").execute()

        # If we get here, the schema exists
        console.print(
            f"[green]✓ Schema verified! Found {result.count} tenants.[/green]"
        )

        # List tenants if any exist
        if result.data:
            table = Table(title="Existing Tenants")
            table.add_column("Name", style="cyan")
            table.add_column("Display Name", style="yellow")

            for tenant in result.data:
                table.add_row(tenant["name"], tenant["display_name"])

            console.print(table)

        return True

    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            console.print("[red]✗ Schema not found. Please create it first.[/red]")
        else:
            console.print(f"[red]Error verifying schema: {e}[/red]")
        return False


def create_test_data(client: Client) -> bool:
    """Create test tenants and data."""
    console.print("\n[yellow]Creating test data...[/yellow]")

    test_tenants = [
        {
            "name": "acme_corp",
            "display_name": "ACME Corporation",
            "drive_folder_id": "acme-corp-folder-id",
            "settings": {"industry": "technology", "size": "enterprise"},
        },
        {
            "name": "globex_inc",
            "display_name": "Globex Inc",
            "drive_folder_id": "globex-inc-folder-id",
            "settings": {"industry": "manufacturing", "size": "mid-market"},
        },
    ]

    try:
        for tenant in test_tenants:
            # Check if tenant exists (in rag schema)
            existing = (
                client.from_("rag.tenants")
                .select("*")
                .eq("name", tenant["name"])
                .execute()
            )

            if not existing.data:
                result = client.from_("rag.tenants").insert(tenant).execute()
                console.print(
                    f"[green]✓ Created tenant: {tenant['display_name']}[/green]"
                )
            else:
                console.print(
                    f"[yellow]Tenant already exists: {tenant['display_name']}[/yellow]"
                )

        return True

    except Exception as e:
        console.print(f"[red]Error creating test data: {e}[/red]")
        return False


def main():
    """Main setup function."""
    console.print(
        Panel.fit(
            "[bold cyan]Multi-Tenant RAG System Setup (Simple Version)[/bold cyan]\n\n"
            "This script helps set up the RAG database schema",
            border_style="cyan",
        )
    )

    # Get Supabase client
    client = get_supabase_client()
    console.print("[green]✓ Connected to Supabase[/green]")

    # Check if schema exists
    if verify_schema(client):
        console.print("\n[green]Schema already exists![/green]")

        # Optionally create test data
        from rich.prompt import Confirm

        if Confirm.ask("\nCreate test tenants?", default=False):
            create_test_data(client)
    else:
        # Show instructions for creating schema
        console.print("\n[bold yellow]Schema Setup Instructions:[/bold yellow]")
        console.print("\n1. Open your Supabase dashboard")
        console.print("2. Go to SQL Editor")
        console.print("3. Copy the contents of: sql/create_rag_system_tables.sql")
        console.print("4. Paste and run in SQL Editor")
        console.print("5. Run this script again to verify\n")

        # Show file location
        sql_file = Path(__file__).parent.parent / "sql" / "create_rag_system_tables.sql"
        if sql_file.exists():
            console.print(f"SQL file location: {sql_file}")

            from rich.prompt import Confirm

            if Confirm.ask("\nOpen SQL file?", default=True):
                import subprocess

                subprocess.run(["open", str(sql_file)])  # macOS
                # For Linux: subprocess.run(["xdg-open", str(sql_file)])
                # For Windows: subprocess.run(["start", str(sql_file)], shell=True)

    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Set up Google OAuth: python scripts/setup_google_oauth.py")
    console.print("2. Deploy MinIO: kubectl apply -f k8s/infrastructure/minio/")
    console.print("3. Test MinIO: python scripts/test_minio_connection.py")
    console.print("4. Deploy Google Drive MCP")

    return 0


if __name__ == "__main__":
    sys.exit(main())
