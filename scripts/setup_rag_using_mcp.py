#!/usr/bin/env python3
"""
Setup RAG system using direct SQL execution via Supabase.

This avoids the schema prefix issue by executing SQL directly.
"""

import os
import sys
from pathlib import Path
import psycopg2
from urllib.parse import urlparse

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def get_db_connection():
    """Get direct PostgreSQL connection from Supabase URL."""
    # Get database URL - try different env var names
    db_url = (
        os.getenv("DATABASE_URL") or 
        os.getenv("SUPABASE_DB_URL") or
        os.getenv("POSTGRES_URL")
    )
    
    if not db_url:
        # Try to construct from individual components
        host = os.getenv("SUPABASE_HOST") or os.getenv("DB_HOST")
        port = os.getenv("SUPABASE_PORT") or os.getenv("DB_PORT") or "5432"
        database = os.getenv("SUPABASE_DB") or os.getenv("DB_NAME") or "postgres"
        user = os.getenv("SUPABASE_USER") or os.getenv("DB_USER") or "postgres"
        password = os.getenv("SUPABASE_PASSWORD") or os.getenv("DB_PASSWORD")
        
        if host and password:
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            console.print("[red]Database connection info not found in .env[/red]")
            console.print("\nPlease add one of these to your .env file:")
            console.print("DATABASE_URL=postgresql://user:password@host:port/database")
            console.print("or")
            console.print("SUPABASE_DB_URL=postgresql://...")
            return None
    
    try:
        console.print(f"[dim]Connecting to database...[/dim]")
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        console.print(f"[red]Failed to connect: {e}[/red]")
        return None


def check_rag_schema(conn):
    """Check if RAG schema exists and list tables."""
    cursor = conn.cursor()
    
    # Check if schema exists
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name = 'rag'
    """)
    
    if not cursor.fetchone():
        return False, []
    
    # List tables in rag schema
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'rag'
        ORDER BY table_name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    return True, tables


def create_public_views(conn):
    """Create views in public schema that point to rag schema tables."""
    console.print("\n[yellow]Creating public schema views for API access...[/yellow]")
    
    cursor = conn.cursor()
    
    # Get all tables in rag schema
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'rag'
        ORDER BY table_name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    
    created_views = []
    
    for table in tables:
        view_name = f"rag_{table}"
        try:
            # Drop existing view if any
            cursor.execute(f"DROP VIEW IF EXISTS public.{view_name} CASCADE")
            
            # Create view
            cursor.execute(f"""
                CREATE VIEW public.{view_name} AS 
                SELECT * FROM rag.{table}
            """)
            
            # Grant permissions
            cursor.execute(f"""
                GRANT ALL ON public.{view_name} TO anon, authenticated
            """)
            
            created_views.append(view_name)
            console.print(f"[green]✓ Created view: {view_name}[/green]")
            
        except Exception as e:
            console.print(f"[red]Failed to create view {view_name}: {e}[/red]")
    
    conn.commit()
    cursor.close()
    
    return created_views


def test_api_access(views):
    """Test if views are accessible via Supabase API."""
    from supabase import create_client
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        console.print("[yellow]Cannot test API access - missing Supabase URL/key[/yellow]")
        return
    
    console.print("\n[yellow]Testing API access to views...[/yellow]")
    
    client = create_client(url, key)
    
    # Test a few key views
    test_views = ["rag_tenants", "rag_documents", "rag_document_types"]
    
    for view in test_views:
        if view not in views:
            continue
            
        try:
            result = client.from_(view).select("*", count="exact").limit(1).execute()
            console.print(f"[green]✓ {view} - accessible ({result.count} rows)[/green]")
        except Exception as e:
            console.print(f"[red]✗ {view} - {str(e)[:50]}...[/red]")


def create_test_tenants(conn):
    """Create test tenants directly in database."""
    console.print("\n[yellow]Creating test tenants...[/yellow]")
    
    cursor = conn.cursor()
    
    test_tenants = [
        ("elf_internal", "ELF Automations Internal", '{"is_internal": true}'),
        ("acme_corp", "ACME Corporation", '{"industry": "technology"}'),
        ("globex_inc", "Globex Inc", '{"industry": "manufacturing"}')
    ]
    
    created = 0
    for name, display_name, settings in test_tenants:
        try:
            # Check if exists
            cursor.execute(
                "SELECT id FROM rag.tenants WHERE name = %s",
                (name,)
            )
            
            if cursor.fetchone():
                console.print(f"[dim]Already exists: {display_name}[/dim]")
            else:
                cursor.execute("""
                    INSERT INTO rag.tenants (name, display_name, settings)
                    VALUES (%s, %s, %s::jsonb)
                """, (name, display_name, settings))
                
                console.print(f"[green]✓ Created: {display_name}[/green]")
                created += 1
                
        except Exception as e:
            console.print(f"[red]Failed to create {name}: {e}[/red]")
    
    conn.commit()
    cursor.close()
    
    console.print(f"\n[green]Created {created} new tenants[/green]")


def main():
    """Main setup function."""
    console.print(Panel.fit(
        "[bold cyan]RAG System Setup - Direct SQL Method[/bold cyan]\n\n"
        "This uses direct database connection to avoid schema issues",
        border_style="cyan"
    ))
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        return 1
    
    console.print("[green]✓ Connected to database[/green]")
    
    # Check RAG schema
    schema_exists, tables = check_rag_schema(conn)
    
    if not schema_exists:
        console.print("\n[red]RAG schema not found![/red]")
        console.print("\nPlease run the SQL from: sql/create_rag_system_tables.sql")
        console.print("in your Supabase SQL Editor first.")
        conn.close()
        return 1
    
    console.print(f"\n[green]✓ RAG schema exists with {len(tables)} tables[/green]")
    
    # Show tables
    table = Table(title="RAG Schema Tables")
    table.add_column("Table Name", style="cyan")
    
    for t in sorted(tables):
        table.add_row(t)
    
    console.print(table)
    
    # Create public views for API access
    from rich.prompt import Confirm
    
    if Confirm.ask("\nCreate public views for API access?", default=True):
        views = create_public_views(conn)
        
        if views:
            console.print(f"\n[green]Created {len(views)} public views[/green]")
            
            # Test API access
            test_api_access(views)
    
    # Create test tenants
    if Confirm.ask("\nCreate test tenants?", default=True):
        create_test_tenants(conn)
    
    # Show usage instructions
    console.print("\n[bold green]Setup Complete! 🎉[/bold green]")
    console.print("\n[bold]Using the RAG System:[/bold]")
    console.print("\nWith views (recommended):")
    console.print('  client.from_("rag_tenants").select("*")')
    console.print('  client.from_("rag_documents").select("*")')
    console.print("\nWith direct SQL (via psycopg2 or similar):")
    console.print('  SELECT * FROM rag.tenants;')
    console.print('  SELECT * FROM rag.documents;')
    
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Update Python code to use rag_ prefixed views")
    console.print("2. Set up Google OAuth: python scripts/setup_google_oauth.py")
    console.print("3. Deploy MinIO: kubectl apply -f k8s/infrastructure/minio/")
    
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())