#!/usr/bin/env python3
"""
Setup MCP Registry in Supabase
Creates tables and migrates existing MCPs from local files
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from supabase import Client, create_client

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

console = Console()


class MCPRegistrySetup:
    """Setup and manage MCP registry in Supabase"""

    def __init__(self):
        load_dotenv()
        self.supabase = self._get_supabase_client()
        self.project_root = Path(__file__).parent.parent

    def _get_supabase_client(self) -> Client:
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            console.print(
                "[red]❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env[/red]"
            )
            sys.exit(1)

        return create_client(url, key)

    def create_schema(self):
        """Create MCP registry schema"""
        console.print("\n[bold cyan]Creating MCP Registry Schema...[/bold cyan]")

        schema_file = self.project_root / "sql" / "create_mcp_registry.sql"
        if not schema_file.exists():
            console.print(f"[red]❌ Schema file not found: {schema_file}[/red]")
            return False

        try:
            # Read schema
            with open(schema_file, "r") as f:
                schema_sql = f.read()

            # Note: Supabase client doesn't support raw SQL execution
            # You'll need to run this via Supabase dashboard or psql
            console.print(
                "[yellow]⚠️  Please run the following SQL in Supabase SQL Editor:[/yellow]"
            )
            console.print(f"[dim]{schema_file}[/dim]")

            return True

        except Exception as e:
            console.print(f"[red]❌ Error creating schema: {e}[/red]")
            return False

    def migrate_existing_mcps(self):
        """Migrate existing MCPs from various sources"""
        console.print("\n[bold cyan]Migrating Existing MCPs...[/bold cyan]")

        # 1. Migrate from AgentGateway config
        self._migrate_from_agentgateway()

        # 2. Migrate from external MCP registry
        self._migrate_from_external_registry()

        # 3. Scan for internal MCPs
        self._scan_internal_mcps()

    def _migrate_from_agentgateway(self):
        """Migrate MCPs from AgentGateway config"""
        config_path = self.project_root / "config" / "agentgateway" / "config.json"

        if not config_path.exists():
            console.print("[yellow]No AgentGateway config found[/yellow]")
            return

        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            mcps = config.get("targets", {}).get("mcp", [])
            console.print(f"Found {len(mcps)} MCPs in AgentGateway config")

            for mcp_config in mcps:
                self._register_mcp_from_gateway(mcp_config)

        except Exception as e:
            console.print(f"[red]Error migrating from AgentGateway: {e}[/red]")

    def _migrate_from_external_registry(self):
        """Migrate external MCPs from marketplace registry"""
        registry_path = self.project_root / "mcp" / "external" / "registry.json"

        if not registry_path.exists():
            console.print("[yellow]No external MCP registry found[/yellow]")
            return

        try:
            with open(registry_path, "r") as f:
                registry = json.load(f)

            console.print(f"Found {len(registry)} external MCPs in registry")

            for name, info in registry.items():
                self._register_external_mcp(name, info)

        except Exception as e:
            console.print(f"[red]Error migrating external MCPs: {e}[/red]")

    def _scan_internal_mcps(self):
        """Scan for internal MCPs in the codebase"""
        # Check TypeScript MCPs
        ts_mcp_dir = self.project_root / "mcp-servers-ts" / "src"
        if ts_mcp_dir.exists():
            for mcp_dir in ts_mcp_dir.iterdir():
                if mcp_dir.is_dir() and (mcp_dir / "server.ts").exists():
                    self._register_internal_mcp_ts(mcp_dir)

        # Check Python MCPs
        py_mcp_dir = self.project_root / "mcps" / "python"
        if py_mcp_dir.exists():
            for mcp_dir in py_mcp_dir.iterdir():
                if mcp_dir.is_dir() and (mcp_dir / "server.py").exists():
                    self._register_internal_mcp_py(mcp_dir)

    def _register_mcp_from_gateway(self, config: Dict[str, Any]):
        """Register an MCP from AgentGateway config"""
        try:
            name = config.get("name", "unknown")

            # Determine protocol and details
            protocol = "stdio"
            install_command = None

            if "stdio" in config:
                protocol = "stdio"
                cmd = config["stdio"].get("cmd", "")
                args = config["stdio"].get("args", [])
                install_command = f"{cmd} {' '.join(args)}"
            elif "http" in config:
                protocol = "http"
            elif "sse" in config:
                protocol = "sse"

            # Check if already exists
            existing = (
                self.supabase.table("mcps").select("*").eq("name", name).execute()
            )

            if not existing.data:
                # Insert new MCP
                mcp_data = {
                    "name": name,
                    "display_name": name.replace("-", " ").title(),
                    "type": "external",  # Assume external for now
                    "protocol": protocol,
                    "install_command": install_command,
                    "status": "active",
                    "config": config,
                }

                result = self.supabase.table("mcps").insert(mcp_data).execute()
                console.print(f"[green]✅ Registered MCP: {name}[/green]")

                # Log the action
                self.supabase.table("mcp_audit_log").insert(
                    {
                        "mcp_id": result.data[0]["id"],
                        "action": "migrated_from_agentgateway",
                        "performed_by": "setup_script",
                    }
                ).execute()
            else:
                console.print(f"[dim]MCP already registered: {name}[/dim]")

        except Exception as e:
            console.print(
                f"[red]Error registering {config.get('name', 'unknown')}: {e}[/red]"
            )

    def _register_external_mcp(self, name: str, info: Dict[str, Any]):
        """Register an external MCP from marketplace"""
        try:
            # Check if already exists
            existing = (
                self.supabase.table("mcps").select("*").eq("name", name).execute()
            )

            if not existing.data:
                mcp_data = {
                    "name": name,
                    "display_name": info.get(
                        "display_name", name.replace("-", " ").title()
                    ),
                    "description": info.get("description", ""),
                    "type": "external",
                    "source": info.get("source", ""),
                    "install_type": "npm",  # Most are npm
                    "status": "active",
                }

                result = self.supabase.table("mcps").insert(mcp_data).execute()
                mcp_id = result.data[0]["id"]

                # Register capabilities as tools
                for capability in info.get("capabilities", []):
                    self.supabase.table("mcp_tools").insert(
                        {
                            "mcp_id": mcp_id,
                            "name": capability,
                            "description": f"{capability} capability",
                        }
                    ).execute()

                console.print(f"[green]✅ Registered external MCP: {name}[/green]")

        except Exception as e:
            console.print(f"[red]Error registering external MCP {name}: {e}[/red]")

    def _register_internal_mcp_ts(self, mcp_dir: Path):
        """Register a TypeScript internal MCP"""
        try:
            name = mcp_dir.name

            # Try to load package.json for details
            package_json = mcp_dir / "package.json"
            description = ""
            if package_json.exists():
                with open(package_json, "r") as f:
                    pkg = json.load(f)
                    description = pkg.get("description", "")

            # Check if already exists
            existing = (
                self.supabase.table("mcps").select("*").eq("name", name).execute()
            )

            if not existing.data:
                mcp_data = {
                    "name": name,
                    "display_name": name.replace("-", " ").title(),
                    "description": description,
                    "type": "internal",
                    "language": "typescript",
                    "source": str(mcp_dir.relative_to(self.project_root)),
                    "status": "active",
                }

                result = self.supabase.table("mcps").insert(mcp_data).execute()
                console.print(
                    f"[green]✅ Registered internal TypeScript MCP: {name}[/green]"
                )

        except Exception as e:
            console.print(f"[red]Error registering TS MCP {mcp_dir.name}: {e}[/red]")

    def _register_internal_mcp_py(self, mcp_dir: Path):
        """Register a Python internal MCP"""
        try:
            name = mcp_dir.name

            # Check if already exists
            existing = (
                self.supabase.table("mcps").select("*").eq("name", name).execute()
            )

            if not existing.data:
                mcp_data = {
                    "name": name,
                    "display_name": name.replace("-", " ").title(),
                    "type": "internal",
                    "language": "python",
                    "source": str(mcp_dir.relative_to(self.project_root)),
                    "status": "active",
                }

                result = self.supabase.table("mcps").insert(mcp_data).execute()
                console.print(
                    f"[green]✅ Registered internal Python MCP: {name}[/green]"
                )

        except Exception as e:
            console.print(
                f"[red]Error registering Python MCP {mcp_dir.name}: {e}[/red]"
            )

    def display_registry_status(self):
        """Display current registry status"""
        console.print("\n[bold cyan]MCP Registry Status[/bold cyan]")

        try:
            # Get counts
            mcps = self.supabase.table("mcps").select("*", count="exact").execute()
            internal = (
                self.supabase.table("mcps")
                .select("*", count="exact")
                .eq("type", "internal")
                .execute()
            )
            external = (
                self.supabase.table("mcps")
                .select("*", count="exact")
                .eq("type", "external")
                .execute()
            )
            active = (
                self.supabase.table("mcps")
                .select("*", count="exact")
                .eq("status", "active")
                .execute()
            )

            # Create status table
            table = Table(title="MCP Registry Overview")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="green")

            table.add_row("Total MCPs", str(mcps.count))
            table.add_row("Internal MCPs", str(internal.count))
            table.add_row("External MCPs", str(external.count))
            table.add_row("Active MCPs", str(active.count))

            console.print(table)

            # Show sample MCPs
            if mcps.data:
                console.print("\n[bold]Sample MCPs:[/bold]")
                for mcp in mcps.data[:5]:
                    status_color = "green" if mcp["status"] == "active" else "yellow"
                    console.print(
                        f"  • {mcp['name']} "
                        f"([{status_color}]{mcp['status']}[/{status_color}]) "
                        f"- {mcp['type']} - {mcp.get('language', 'N/A')}"
                    )

        except Exception as e:
            console.print(f"[red]Error getting registry status: {e}[/red]")


def main():
    """Main setup function"""
    console.print(
        Panel.fit(
            "[bold cyan]MCP Registry Setup[/bold cyan]\n"
            "Setting up centralized MCP registry in Supabase",
            border_style="cyan",
        )
    )

    setup = MCPRegistrySetup()

    # Step 1: Create schema
    console.print("\n[bold]Step 1: Create Schema[/bold]")
    setup.create_schema()

    # Wait for user to create schema
    console.print(
        "\n[yellow]Please create the schema in Supabase before continuing.[/yellow]"
    )
    input("Press Enter when schema is created...")

    # Step 2: Migrate existing MCPs
    console.print("\n[bold]Step 2: Migrate Existing MCPs[/bold]")
    setup.migrate_existing_mcps()

    # Step 3: Display status
    setup.display_registry_status()

    console.print("\n[green]✅ MCP Registry setup complete![/green]")
    console.print("\nNext steps:")
    console.print("1. Update mcp_factory.py to register new MCPs in Supabase")
    console.print("2. Update mcp_marketplace.py to use Supabase registry")
    console.print("3. Enhance AgentGateway to read from Supabase")


if __name__ == "__main__":
    main()
