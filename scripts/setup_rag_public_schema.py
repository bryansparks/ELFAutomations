#!/usr/bin/env python3
"""
Setup RAG system using tables in public schema.

This version works with the rag_ prefixed tables in the public schema.
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
from supabase import create_client, Client

console = Console()


def get_supabase_client() -> Client:
    """Get Supabase client from .env configuration."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        console.print("[red]Error: SUPABASE_URL and SUPABASE_ANON_KEY not found in .env file![/red]")
        console.print("\nMake sure your .env file contains:")
        console.print("SUPABASE_URL=https://your-project.supabase.co")
        console.print("SUPABASE_ANON_KEY=your-anon-key")
        sys.exit(1)
    
    console.print(f"[dim]Using Supabase URL: {url[:30]}...[/dim]")
    return create_client(url, key)


def verify_tables(client: Client) -> dict:
    """Verify which RAG tables exist in public schema."""
    tables_to_check = [
        "rag_tenants", "rag_workspaces", "rag_documents", "rag_document_chunks",
        "rag_processing_queue", "rag_entities", "rag_relationships",
        "rag_search_queries", "rag_api_usage", "rag_document_types"
    ]
    
    results = {}
    for table in tables_to_check:
        try:
            # Try to access table in public schema
            result = client.from_(table).select("*", count="exact").limit(1).execute()
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
            "settings": {"is_internal": True, "unlimited_quota": True}
        },
        {
            "name": "acme_corp",
            "display_name": "ACME Corporation",
            "drive_folder_id": "acme-corp-folder-id",
            "settings": {"industry": "technology", "size": "enterprise"}
        },
        {
            "name": "globex_inc",
            "display_name": "Globex Inc",
            "drive_folder_id": "globex-inc-folder-id",
            "settings": {"industry": "manufacturing", "size": "mid-market"}
        },
        {
            "name": "stanford_edu",
            "display_name": "Stanford University",
            "drive_folder_id": "stanford-edu-folder-id",
            "settings": {"industry": "education", "size": "large"}
        }
    ]
    
    created = 0
    existing = 0
    
    for tenant in test_tenants:
        try:
            # Check if exists (using public schema table)
            result = client.from_("rag_tenants").select("*").eq("name", tenant["name"]).execute()
            
            if not result.data:
                client.from_("rag_tenants").insert(tenant).execute()
                console.print(f"[green]✓ Created: {tenant['display_name']}[/green]")
                created += 1
            else:
                console.print(f"[dim]Already exists: {tenant['display_name']}[/dim]")
                existing += 1
                
        except Exception as e:
            console.print(f"[red]Failed to create {tenant['name']}: {e}[/red]")
    
    console.print(f"\n[green]Created {created} new tenants, {existing} already existed[/green]")


def show_tenant_details(client: Client):
    """Show details of existing tenants."""
    try:
        tenants = client.from_("rag_tenants").select("*").execute()
        
        if tenants.data:
            table = Table(title="Configured Tenants")
            table.add_column("Name", style="cyan")
            table.add_column("Display Name", style="yellow")
            table.add_column("Status", style="green")
            table.add_column("Drive Folder", style="blue")
            
            for tenant in tenants.data:
                table.add_row(
                    tenant["name"],
                    tenant["display_name"],
                    tenant.get("status", "active"),
                    tenant.get("drive_folder_id", "Not Set")[:20] + "..." if tenant.get("drive_folder_id") else "Not Set"
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error fetching tenants: {e}[/red]")


def show_document_types(client: Client):
    """Show configured document types."""
    try:
        doc_types = client.from_("rag_document_types").select("*").execute()
        
        if doc_types.data:
            table = Table(title="Document Types")
            table.add_column("Name", style="cyan")
            table.add_column("Display Name", style="yellow")
            table.add_column("Primary Storage", style="green")
            
            for dt in doc_types.data:
                storage = dt.get("storage_strategy", {})
                primary = storage.get("primary", "unknown") if isinstance(storage, dict) else "unknown"
                table.add_row(dt["name"], dt["display_name"], primary)
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error fetching document types: {e}[/red]")


def check_rls_status(client: Client):
    """Check if RLS is enabled on RAG tables."""
    # This is a simple check - we'll try to insert and see if RLS blocks it
    try:
        # Try a simple query
        result = client.from_("rag_tenants").select("count", count="exact").execute()
        return True, result.count
    except Exception as e:
        if "row-level security" in str(e).lower():
            return True, 0  # RLS is enabled
        return False, 0  # Other error


def main():
    """Main setup function."""
    console.print(Panel.fit(
        "[bold cyan]Multi-Tenant RAG System Setup[/bold cyan]\n\n"
        "Using public schema tables with rag_ prefix",
        border_style="cyan"
    ))
    
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
        console.print("[green]✓ Successfully connected to Supabase[/green]")
    except Exception as e:
        console.print(f"[red]Connection error: {e}[/red]")
        return 1
    
    # Check schema
    console.print("\n[yellow]Checking RAG tables...[/yellow]")
    
    # Verify tables
    table_results = verify_tables(client)
    all_tables_exist = show_table_status(table_results)
    
    if not all_tables_exist:
        console.print("\n[yellow]Some tables are missing![/yellow]")
        console.print("\nPlease run one of these SQL files in Supabase:")
        console.print("1. sql/create_rag_system_tables_public.sql (recommended)")
        console.print("   - Creates tables with rag_ prefix in public schema")
        console.print("2. sql/create_rag_system_tables.sql (original)")
        console.print("   - Creates tables in rag schema (requires additional setup)")
        
        from rich.prompt import Confirm
        if Confirm.ask("\nOpen SQL file location?", default=True):
            import subprocess
            sql_dir = Path(__file__).parent.parent / "sql"
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(sql_dir)])
            elif sys.platform.startswith("linux"):
                subprocess.run(["xdg-open", str(sql_dir)])
            elif sys.platform == "win32":
                subprocess.run(["explorer", str(sql_dir)])
        
        return 1
    
    console.print("\n[green]✅ All RAG tables exist![/green]")
    
    # Show existing data
    show_document_types(client)
    show_tenant_details(client)
    
    # Create test data
    from rich.prompt import Confirm
    if Confirm.ask("\nCreate test tenants?", default=True):
        # Check if we need to handle RLS
        try:
            # Try to create a test entry
            test_result = client.from_("rag_tenants").select("count", count="exact").execute()
            
            # If we can query, try to insert
            create_test_tenants(client)
            # Refresh tenant display
            show_tenant_details(client)
            
        except Exception as e:
            if "row-level security" in str(e).lower():
                console.print("\n[yellow]Row Level Security is blocking tenant creation.[/yellow]")
                console.print("\nTo fix this, run one of these SQL scripts in Supabase:")
                console.print("1. [bold]sql/disable_rag_rls_temporary.sql[/bold] - Temporarily disable RLS")
                console.print("2. [bold]sql/fix_rag_rls_policies.sql[/bold] - Update RLS policies")
                console.print("\nAfter creating tenants, you can re-enable RLS with:")
                console.print("3. [bold]sql/enable_rag_rls.sql[/bold]")
                
                if Confirm.ask("\nOpen SQL directory?", default=True):
                    import subprocess
                    sql_dir = Path(__file__).parent.parent / "sql"
                    if sys.platform == "darwin":  # macOS
                        subprocess.run(["open", str(sql_dir)])
                    elif sys.platform.startswith("linux"):
                        subprocess.run(["xdg-open", str(sql_dir)])
                    elif sys.platform == "win32":
                        subprocess.run(["explorer", str(sql_dir)])
            else:
                console.print(f"\n[red]Error creating tenants: {e}[/red]")
    
    # Show usage examples
    console.print("\n[bold green]Setup Complete! 🎉[/bold green]")
    console.print("\n[bold]Python Usage Examples:[/bold]")
    console.print("""
```python
# Get all tenants
tenants = client.from_("rag_tenants").select("*").execute()

# Create a document
doc = client.from_("rag_documents").insert({
    "tenant_id": tenant_id,
    "filename": "test.pdf",
    "source_type": "upload",
    "source_id": "unique-id"
}).execute()

# Query with tenant isolation
docs = client.from_("rag_documents")\\
    .select("*")\\
    .eq("tenant_id", tenant_id)\\
    .execute()
```
""")
    
    # Show next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Set up Google OAuth credentials:")
    console.print("   python scripts/setup_google_oauth.py")
    console.print("\n2. Deploy MinIO for document storage:")
    console.print("   kubectl apply -f k8s/infrastructure/minio/")
    console.print("\n3. Test MinIO connection:")
    console.print("   python scripts/test_minio_connection.py")
    console.print("\n4. Build and deploy the Google Drive MCP:")
    console.print("   cd mcps/google-drive-watcher && npm install")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())