#!/usr/bin/env python3
"""
Quick test to verify RAG schema access in Supabase.

This helps diagnose if the issue is with schema access or table names.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from supabase import create_client, Client

console = Console()


def test_schema_access():
    """Test different ways to access the RAG schema."""
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        console.print("[red]Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env[/red]")
        return
    
    console.print(f"[dim]Connecting to: {url[:30]}...[/dim]\n")
    client = create_client(url, key)
    
    # Test 1: Direct table access with schema
    console.print("[bold]Test 1: Direct access with schema prefix[/bold]")
    try:
        result = client.from_("rag.tenants").select("*", count="exact").limit(1).execute()
        console.print(f"[green]✓ Success! Found {result.count} rows in rag.tenants[/green]")
        if result.data:
            console.print(f"  Sample: {result.data[0].get('name', 'N/A')}")
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]")
    
    # Test 2: Try without schema prefix (should fail)
    console.print("\n[bold]Test 2: Access without schema prefix[/bold]")
    try:
        result = client.from_("tenants").select("*", count="exact").limit(1).execute()
        console.print(f"[yellow]⚠ Unexpected success - table accessible without schema[/yellow]")
    except Exception as e:
        console.print(f"[green]✓ Expected failure: {str(e)[:100]}...[/green]")
    
    # Test 3: RPC function access
    console.print("\n[bold]Test 3: RPC function access[/bold]")
    try:
        # Try to call the set_tenant_context function
        result = client.rpc("rag.get_current_tenant").execute()
        console.print(f"[green]✓ RPC function accessible[/green]")
    except Exception as e:
        console.print(f"[yellow]RPC function not accessible: {str(e)[:100]}[/yellow]")
    
    # Test 4: List all accessible tables
    console.print("\n[bold]Test 4: Check table existence via count[/bold]")
    tables = [
        "rag.tenants",
        "rag.workspaces", 
        "rag.documents",
        "rag.document_chunks",
        "rag.processing_queue",
        "rag.document_types"
    ]
    
    accessible = []
    for table in tables:
        try:
            result = client.from_(table).select("*", count="exact").limit(0).execute()
            accessible.append(f"{table} ({result.count} rows)")
            console.print(f"[green]✓ {table} - {result.count} rows[/green]")
        except Exception as e:
            console.print(f"[red]✗ {table} - {str(e)[:50]}...[/red]")
    
    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"Accessible tables: {len(accessible)}/{len(tables)}")
    
    if len(accessible) == len(tables):
        console.print("\n[green]✅ All RAG tables are accessible![/green]")
        console.print("\nYou can now run: python scripts/setup_rag_with_env.py")
    else:
        console.print("\n[yellow]⚠ Some tables are not accessible[/yellow]")
        console.print("\nPossible issues:")
        console.print("1. Schema might not be created yet")
        console.print("2. RLS policies might be blocking access")
        console.print("3. The anon key might not have proper permissions")
        console.print("\nTry running the SQL directly in Supabase SQL Editor")


if __name__ == "__main__":
    test_schema_access()