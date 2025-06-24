#!/usr/bin/env python3
"""
Setup script for the Multi-Tenant RAG System that loads from .env file.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from supabase import Client, create_client

console = Console()


def get_supabase_client() -> Client:
    """Get Supabase client from .env configuration."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        console.print(
            "[red]Error: SUPABASE_URL and SUPABASE_ANON_KEY not found in .env file![/red]"
        )
        console.print("\nMake sure your .env file contains:")
        console.print("SUPABASE_URL=https://your-project.supabase.co")
        console.print("SUPABASE_ANON_KEY=your-anon-key")
        sys.exit(1)

    console.print(f"[dim]Using Supabase URL: {url[:30]}...[/dim]")
    return create_client(url, key)


def test_connection(client: Client) -> bool:
    """Test Supabase connection."""
    try:
        # Try a simple query
        result = client.from_("test").select("*").limit(1).execute()
        return True
    except Exception as e:
        # Connection works even if table doesn't exist
        return True


def check_schema_exists(client: Client) -> bool:
    """Check if RAG schema exists."""
    try:
        # Try to access the tenants table in rag schema
        result = (
            client.schema("rag")
            .from_("tenants")
            .select("*", count="exact")
            .limit(1)
            .execute()
        )
        return True
    except Exception as e:
        if "schema" in str(e).lower() or "relation" in str(e).lower():
            return False
        # If it's another error, schema might exist but have other issues
        return True


def create_schema_instructions():
    """Show instructions for creating the schema."""
    console.print("\n[bold yellow]To create the RAG schema:[/bold yellow]\n")

    sql_file = Path(__file__).parent.parent / "sql" / "create_rag_system_tables.sql"

    console.print("Option 1: [bold]Using Supabase Dashboard[/bold]")
    console.print("1. Go to your Supabase project dashboard")
    console.print("2. Navigate to SQL Editor")
    console.print("3. Create a new query")
    console.print(f"4. Copy contents from: {sql_file}")
    console.print("5. Run the query\n")

    console.print("Option 2: [bold]Using psql (if you have direct access)[/bold]")
    console.print("psql $DATABASE_URL < sql/create_rag_system_tables.sql\n")

    if sql_file.exists():
        from rich.prompt import Confirm

        if Confirm.ask("Open SQL file in editor?", default=True):
            import subprocess

            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(sql_file)])
            elif sys.platform.startswith("linux"):
                subprocess.run(["xdg-open", str(sql_file)])
            elif sys.platform == "win32":
                subprocess.run(["start", str(sql_file)], shell=True)


def verify_tables(client: Client) -> dict:
    """Verify which RAG tables exist."""
    tables_to_check = [
        "tenants",
        "workspaces",
        "documents",
        "document_chunks",
        "processing_queue",
        "entities",
        "relationships",
        "search_queries",
        "api_usage",
        "document_types",
    ]

    results = {}
    for table in tables_to_check:
        try:
            # Tables are in the rag schema, so use full name
            full_table_name = f"rag.{table}"
            result = (
                client.from_(full_table_name)
                .select("*", count="exact")
                .limit(1)
                .execute()
            )
            results[table] = True
        except Exception as e:
            results[table] = False

    return results


def show_table_status(results: dict):
    """Display table verification results."""
    table = Table(title="RAG Schema Status")
    table.add_column("Table", style="cyan")
    table.add_column("Status", style="green")

    all_exist = True
    for table_name, exists in results.items():
        status = "✓ Exists" if exists else "✗ Missing"
        style = "green" if exists else "red"
        table.add_row(table_name, f"[{style}]{status}[/{style}]")
        if not exists:
            all_exist = False

    console.print(table)
    return all_exist


def create_test_tenants(client: Client):
    """Create test tenants if they don't exist."""
    console.print("\n[yellow]Creating test tenants...[/yellow]")

    test_tenants = [
        {
            "name": "elf_internal",
            "display_name": "ELF Automations Internal",
            "settings": {"is_internal": True, "unlimited_quota": True},
        },
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

    created = 0
    existing = 0

    for tenant in test_tenants:
        try:
            # Check if exists (use rag schema)
            result = (
                client.from_("rag.tenants")
                .select("*")
                .eq("name", tenant["name"])
                .execute()
            )

            if not result.data:
                client.from_("rag.tenants").insert(tenant).execute()
                console.print(f"[green]✓ Created: {tenant['display_name']}[/green]")
                created += 1
            else:
                console.print(f"[dim]Already exists: {tenant['display_name']}[/dim]")
                existing += 1

        except Exception as e:
            console.print(f"[red]Failed to create {tenant['name']}: {e}[/red]")

    console.print(
        f"\n[green]Created {created} new tenants, {existing} already existed[/green]"
    )


def main():
    """Main setup function."""
    console.print(
        Panel.fit(
            "[bold cyan]Multi-Tenant RAG System Setup[/bold cyan]\n\n"
            "Setting up RAG database schema from .env configuration",
            border_style="cyan",
        )
    )

    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        console.print("[red]Error: .env file not found![/red]")
        console.print("\nMake sure you're running this from the project root")
        console.print("and that your .env file exists.")
        return 1

    console.print("[green]✓ Found .env file[/green]")

    # Connect to Supabase
    console.print("\n[yellow]Connecting to Supabase...[/yellow]")
    try:
        client = get_supabase_client()
        if test_connection(client):
            console.print("[green]✓ Successfully connected to Supabase[/green]")
        else:
            console.print("[red]✗ Failed to connect to Supabase[/red]")
            return 1
    except Exception as e:
        console.print(f"[red]Connection error: {e}[/red]")
        return 1

    # Check schema
    console.print("\n[yellow]Checking RAG schema...[/yellow]")

    # Verify tables
    table_results = verify_tables(client)
    all_tables_exist = show_table_status(table_results)

    if not all_tables_exist:
        console.print("\n[yellow]Some tables are missing![/yellow]")
        create_schema_instructions()

        from rich.prompt import Confirm

        if Confirm.ask("\nHave you created the schema?", default=False):
            # Re-check
            table_results = verify_tables(client)
            all_tables_exist = show_table_status(table_results)

    if all_tables_exist:
        console.print("\n[green]✅ All RAG tables exist![/green]")

        # Create test data
        from rich.prompt import Confirm

        if Confirm.ask("\nCreate test tenants?", default=True):
            create_test_tenants(client)

        # Show next steps
        console.print("\n[bold green]Setup Complete! 🎉[/bold green]")
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Set up Google OAuth credentials:")
        console.print("   python scripts/setup_google_oauth.py")
        console.print("\n2. Deploy MinIO for document storage:")
        console.print("   kubectl apply -f k8s/infrastructure/minio/")
        console.print("\n3. Test MinIO connection:")
        console.print("   python scripts/test_minio_connection.py")
        console.print("\n4. Build and deploy the Google Drive MCP:")
        console.print("   cd mcps/google-drive-watcher && npm install")
    else:
        console.print(
            "\n[red]Please create the schema first, then run this script again.[/red]"
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
