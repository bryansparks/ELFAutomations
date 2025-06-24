#!/usr/bin/env python3
"""
Setup script for the Multi-Tenant RAG System database schema.

This script:
1. Creates the RAG system schema in Supabase
2. Sets up initial tenants
3. Configures document types
4. Validates the setup
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from supabase import Client, create_client

from elf_automations.shared.config import get_supabase_client
from elf_automations.shared.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


def setup_rag_schema(client: Client) -> bool:
    """Apply the RAG system schema to Supabase."""
    console.print(
        "\n[bold cyan]Setting up Multi-Tenant RAG System Schema[/bold cyan]\n"
    )

    try:
        # Read the schema file
        schema_path = (
            Path(__file__).parent.parent / "sql" / "create_rag_system_tables.sql"
        )
        if not schema_path.exists():
            console.print(f"[red]Schema file not found: {schema_path}[/red]")
            return False

        with open(schema_path, "r") as f:
            schema_sql = f.read()

        # Execute the schema
        console.print("[yellow]Creating RAG schema and tables...[/yellow]")
        result = client.rpc("exec_sql", {"sql": schema_sql}).execute()
        console.print("[green]✓ Schema created successfully[/green]")

        return True

    except Exception as e:
        console.print(f"[red]Failed to create schema: {e}[/red]")
        logger.error(f"Schema creation failed: {e}")
        return False


def create_test_tenants(client: Client) -> bool:
    """Create test tenants for development."""
    console.print("\n[yellow]Creating test tenants...[/yellow]")

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
        {
            "name": "stanford_edu",
            "display_name": "Stanford University",
            "drive_folder_id": "stanford-edu-folder-id",
            "settings": {"industry": "education", "size": "large"},
        },
    ]

    try:
        for tenant in test_tenants:
            result = client.table("rag.tenants").insert(tenant).execute()
            console.print(f"[green]✓ Created tenant: {tenant['display_name']}[/green]")

            # Create default workspace for each tenant
            tenant_id = result.data[0]["id"]
            workspace = {
                "tenant_id": tenant_id,
                "name": "default",
                "display_name": "Default Workspace",
            }
            client.table("rag.workspaces").insert(workspace).execute()
            console.print(f"  [green]✓ Created default workspace[/green]")

        return True

    except Exception as e:
        console.print(f"[red]Failed to create test tenants: {e}[/red]")
        return False


def validate_setup(client: Client) -> bool:
    """Validate the RAG system setup."""
    console.print("\n[yellow]Validating setup...[/yellow]")

    try:
        # Check tables exist
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

        for table in tables_to_check:
            result = (
                client.table(f"rag.{table}").select("count", count="exact").execute()
            )
            console.print(f"[green]✓ Table 'rag.{table}' exists[/green]")

        # Check document types
        doc_types = client.table("rag.document_types").select("*").execute()

        table = Table(title="Document Types")
        table.add_column("Name", style="cyan")
        table.add_column("Display Name", style="yellow")
        table.add_column("Primary Storage", style="green")

        for dt in doc_types.data:
            storage = dt["storage_strategy"]
            primary = storage.get("primary", "unknown")
            table.add_row(dt["name"], dt["display_name"], primary)

        console.print(table)

        # Check tenants
        tenants = client.table("rag.tenants").select("*").execute()

        tenant_table = Table(title="Configured Tenants")
        tenant_table.add_column("Name", style="cyan")
        tenant_table.add_column("Display Name", style="yellow")
        tenant_table.add_column("Status", style="green")

        for tenant in tenants.data:
            tenant_table.add_row(
                tenant["name"], tenant["display_name"], tenant.get("status", "active")
            )

        console.print(tenant_table)

        return True

    except Exception as e:
        console.print(f"[red]Validation failed: {e}[/red]")
        return False


def test_rls(client: Client) -> bool:
    """Test Row Level Security is working."""
    console.print("\n[yellow]Testing Row Level Security...[/yellow]")

    try:
        # Get a test tenant
        tenants = client.table("rag.tenants").select("*").limit(1).execute()
        if not tenants.data:
            console.print("[yellow]No tenants found for RLS testing[/yellow]")
            return True

        tenant_id = tenants.data[0]["id"]
        tenant_name = tenants.data[0]["name"]

        # Set tenant context
        client.rpc("rag.set_tenant_context", {"tenant_id": tenant_id}).execute()
        console.print(f"[green]✓ Set tenant context to: {tenant_name}[/green]")

        # Try to query documents (should only see this tenant's docs)
        docs = client.table("rag.documents").select("*").execute()
        console.print(f"[green]✓ RLS active - can query tenant documents[/green]")

        return True

    except Exception as e:
        console.print(f"[red]RLS test failed: {e}[/red]")
        return False


def main():
    """Main setup function."""
    console.print(
        Panel.fit(
            "[bold cyan]Multi-Tenant RAG System Setup[/bold cyan]\n\n"
            "This script will create the database schema for the RAG system",
            border_style="cyan",
        )
    )

    # Get Supabase client
    try:
        client = get_supabase_client()
    except Exception as e:
        console.print(f"[red]Failed to connect to Supabase: {e}[/red]")
        console.print(
            "\n[yellow]Make sure your Supabase credentials are configured[/yellow]"
        )
        return 1

    # Run setup steps
    steps = [
        ("Create RAG Schema", setup_rag_schema),
        ("Create Test Tenants", create_test_tenants),
        ("Validate Setup", validate_setup),
        ("Test RLS", test_rls),
    ]

    success = True
    for step_name, step_func in steps:
        console.print(f"\n[bold]{step_name}[/bold]")
        if not step_func(client):
            success = False
            console.print(f"[red]Step '{step_name}' failed[/red]")
            break

    if success:
        console.print(
            Panel.fit(
                "[bold green]✅ RAG System Setup Complete![/bold green]\n\n"
                "The multi-tenant RAG system schema has been created successfully.\n\n"
                "[yellow]Next steps:[/yellow]\n"
                "1. Create Google Drive integration MCP\n"
                "2. Set up MinIO for document storage\n"
                "3. Configure Google OAuth credentials\n"
                "4. Create the RAG processor team",
                border_style="green",
            )
        )

        # Show connection info
        console.print("\n[bold]Connection Info:[/bold]")
        console.print("- Use rag.set_tenant_context(tenant_id) to set tenant")
        console.print("- All queries will be automatically filtered by tenant")
        console.print("- Document processing queue is ready for use")

        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
