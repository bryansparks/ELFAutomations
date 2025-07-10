#!/usr/bin/env python3
"""
RAG Watcher Setup
Automated setup and management for document watchers.

Features:
- Google Drive folder watcher configuration
- Multi-tenant folder setup
- OAuth token management
- Periodic sync scheduling
- Watcher health monitoring
"""

import argparse
import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from elf_automations.shared.config import settings
from elf_automations.shared.mcp import MCPClient
from elf_automations.shared.utils import get_supabase_client
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


class RAGWatcherSetup:
    """Setup and manage RAG document watchers"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.mcp_client = MCPClient()
        self.config_file = Path.home() / ".elf" / "rag_watchers.json"
        self.config_file.parent.mkdir(exist_ok=True)

    async def setup_google_drive_watcher(self) -> Dict[str, Any]:
        """Setup Google Drive watcher MCP"""
        console.print("\n[bold blue]Google Drive Watcher Setup[/bold blue]\n")

        # Check if MCP is available
        console.print("[yellow]Checking Google Drive MCP availability...[/yellow]")

        try:
            # Test MCP connection
            result = await self.mcp_client.call_tool(
                "google-drive-watcher", "get_status", {}
            )

            console.print("[green]Google Drive MCP is available![/green]")

            # Check OAuth status
            if not result.get("oauth_configured"):
                console.print(
                    "\n[yellow]OAuth not configured. Starting setup...[/yellow]"
                )
                await self._setup_oauth()
            else:
                console.print("[green]OAuth is already configured[/green]")

            return {"status": "success", "mcp_status": result}

        except Exception as e:
            console.print(f"[red]Google Drive MCP not available: {str(e)}[/red]")
            console.print(
                "\n[yellow]Please ensure the Google Drive MCP is deployed:[/yellow]"
            )
            console.print(
                "1. Deploy via GitOps: ./scripts/deploy_google_drive_mcp_gitops.sh"
            )
            console.print("2. Check pod status: kubectl get pods -n elf-mcps")

            return {"status": "error", "error": str(e)}

    async def _setup_oauth(self):
        """Setup OAuth for Google Drive"""
        try:
            # Get auth URL
            result = await self.mcp_client.call_tool(
                "google-drive-watcher", "get_auth_url", {}
            )

            auth_url = result.get("auth_url")
            if auth_url:
                console.print(f"\n[bold]Please visit this URL to authorize:[/bold]")
                console.print(f"[cyan]{auth_url}[/cyan]")

                auth_code = Prompt.ask("\nEnter the authorization code")

                # Exchange code for tokens
                result = await self.mcp_client.call_tool(
                    "google-drive-watcher", "authorize", {"code": auth_code}
                )

                if result.get("success"):
                    console.print("[green]OAuth setup completed successfully![/green]")
                else:
                    console.print(
                        f"[red]OAuth setup failed: {result.get('error')}[/red]"
                    )

        except Exception as e:
            console.print(f"[red]OAuth setup error: {str(e)}[/red]")

    async def setup_tenant_folders(self) -> Dict[str, Any]:
        """Setup folders for each tenant"""
        console.print("\n[bold blue]Tenant Folder Setup[/bold blue]\n")

        # Get all tenants
        tenants = (
            self.supabase.table("rag_tenants")
            .select("*")
            .eq("status", "active")
            .execute()
        )

        if not tenants.data:
            console.print("[yellow]No active tenants found[/yellow]")
            return {"status": "no_tenants"}

        # Display current tenants
        table = Table(title="Active Tenants")
        table.add_column("Name", style="cyan")
        table.add_column("Display Name", style="magenta")
        table.add_column("Drive Folder", style="green")

        for tenant in tenants.data:
            folder_status = "✓" if tenant.get("drive_folder_id") else "✗"
            table.add_row(tenant["name"], tenant["display_name"], folder_status)

        console.print(table)

        # Setup folders for tenants without them
        setup_results = []

        for tenant in tenants.data:
            if not tenant.get("drive_folder_id"):
                console.print(
                    f"\n[yellow]Setting up folder for {tenant['display_name']}...[/yellow]"
                )

                folder_id = Prompt.ask(
                    f"Enter Google Drive folder ID for {tenant['display_name']} (or 'skip')"
                )

                if folder_id.lower() != "skip":
                    result = await self._add_watch_folder(
                        tenant["id"], tenant["name"], folder_id
                    )
                    setup_results.append(result)

        return {
            "status": "success",
            "tenants_processed": len(tenants.data),
            "folders_setup": len(setup_results),
        }

    async def _add_watch_folder(
        self, tenant_id: str, tenant_name: str, folder_id: str
    ) -> Dict[str, Any]:
        """Add a folder to watch"""
        try:
            # Add to MCP watcher
            result = await self.mcp_client.call_tool(
                "google-drive-watcher",
                "add_watch_folder",
                {"folderId": folder_id, "tenantName": tenant_name},
            )

            if result.get("success"):
                # Update tenant record
                self.supabase.table("rag_tenants").update(
                    {
                        "drive_folder_id": folder_id,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ).eq("id", tenant_id).execute()

                console.print(f"[green]Added folder for {tenant_name}[/green]")

                return {
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "folder_id": folder_id,
                    "status": "success",
                }
            else:
                console.print(f"[red]Failed to add folder: {result.get('error')}[/red]")
                return {
                    "tenant_id": tenant_id,
                    "status": "error",
                    "error": result.get("error"),
                }

        except Exception as e:
            console.print(f"[red]Error adding folder: {str(e)}[/red]")
            return {"tenant_id": tenant_id, "status": "error", "error": str(e)}

    async def configure_sync_schedule(self) -> Dict[str, Any]:
        """Configure synchronization schedule"""
        console.print("\n[bold blue]Sync Schedule Configuration[/bold blue]\n")

        # Get current schedule
        try:
            status = await self.mcp_client.call_tool(
                "google-drive-watcher", "get_status", {}
            )

            current_interval = status.get("monitoring_interval", 300)
            console.print(
                f"Current sync interval: [cyan]{current_interval} seconds[/cyan]"
            )

            # Ask for new interval
            new_interval = Prompt.ask(
                "Enter new sync interval in seconds (60-3600)",
                default=str(current_interval),
            )

            try:
                interval = int(new_interval)
                if 60 <= interval <= 3600:
                    # Start monitoring with new interval
                    result = await self.mcp_client.call_tool(
                        "google-drive-watcher",
                        "start_monitoring",
                        {"intervalSeconds": interval},
                    )

                    if result.get("success"):
                        console.print(
                            f"[green]Sync schedule updated to {interval} seconds[/green]"
                        )

                        # Save to config
                        self._save_config({"sync_interval": interval})

                        return {"status": "success", "interval": interval}
                    else:
                        console.print(
                            f"[red]Failed to update schedule: {result.get('error')}[/red]"
                        )
                        return {"status": "error", "error": result.get("error")}
                else:
                    console.print(
                        "[red]Interval must be between 60 and 3600 seconds[/red]"
                    )
                    return {"status": "error", "error": "Invalid interval"}

            except ValueError:
                console.print("[red]Invalid number[/red]")
                return {"status": "error", "error": "Invalid number"}

        except Exception as e:
            console.print(f"[red]Error configuring schedule: {str(e)}[/red]")
            return {"status": "error", "error": str(e)}

    async def check_watcher_health(self) -> Dict[str, Any]:
        """Check health of all watchers"""
        console.print("\n[bold blue]Watcher Health Check[/bold blue]\n")

        health_status = {"timestamp": datetime.utcnow().isoformat(), "watchers": {}}

        # Check Google Drive watcher
        try:
            status = await self.mcp_client.call_tool(
                "google-drive-watcher", "get_status", {}
            )

            health_status["watchers"]["google_drive"] = {
                "status": "healthy" if status.get("is_monitoring") else "stopped",
                "oauth_configured": status.get("oauth_configured", False),
                "folders_watched": len(status.get("watched_folders", [])),
                "last_sync": status.get("last_sync"),
                "monitoring_interval": status.get("monitoring_interval"),
            }

            # Display status
            table = Table(title="Google Drive Watcher Status")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="magenta")

            gd_status = health_status["watchers"]["google_drive"]

            status_color = "green" if gd_status["status"] == "healthy" else "red"
            table.add_row(
                "Status", f"[{status_color}]{gd_status['status']}[/{status_color}]"
            )
            table.add_row(
                "OAuth Configured", "✓" if gd_status["oauth_configured"] else "✗"
            )
            table.add_row("Folders Watched", str(gd_status["folders_watched"]))
            table.add_row("Monitoring Interval", f"{gd_status['monitoring_interval']}s")

            if gd_status["last_sync"]:
                table.add_row("Last Sync", gd_status["last_sync"])

            console.print(table)

            # Check recent documents
            await self._check_recent_documents()

        except Exception as e:
            console.print(f"[red]Error checking Google Drive watcher: {str(e)}[/red]")
            health_status["watchers"]["google_drive"] = {
                "status": "error",
                "error": str(e),
            }

        return health_status

    async def _check_recent_documents(self):
        """Check recently discovered documents"""
        # Get documents from last 24 hours
        window_start = datetime.utcnow() - timedelta(hours=24)

        recent_docs = (
            self.supabase.table("rag_documents")
            .select("filename, source_type, created_at, status")
            .eq("source_type", "google_drive")
            .gte("created_at", window_start.isoformat())
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        if recent_docs.data:
            console.print("\n[bold]Recent Documents (Last 24h):[/bold]")

            doc_table = Table()
            doc_table.add_column("Filename", style="cyan")
            doc_table.add_column("Status", style="magenta")
            doc_table.add_column("Created", style="green")

            for doc in recent_docs.data:
                status_color = "green" if doc["status"] == "completed" else "yellow"
                created = datetime.fromisoformat(
                    doc["created_at"].replace("Z", "+00:00")
                )
                time_ago = datetime.utcnow() - created.replace(tzinfo=None)

                doc_table.add_row(
                    doc["filename"][:40] + "..."
                    if len(doc["filename"]) > 40
                    else doc["filename"],
                    f"[{status_color}]{doc['status']}[/{status_color}]",
                    f"{time_ago.total_seconds() / 3600:.1f}h ago",
                )

            console.print(doc_table)
        else:
            console.print(
                "\n[yellow]No documents discovered in the last 24 hours[/yellow]"
            )

    async def manage_oauth_tokens(self) -> Dict[str, Any]:
        """Manage OAuth tokens"""
        console.print("\n[bold blue]OAuth Token Management[/bold blue]\n")

        options = [
            "1. Refresh tokens",
            "2. Revoke tokens",
            "3. Re-authenticate",
            "4. Back",
        ]

        for option in options:
            console.print(option)

        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4"])

        if choice == "1":
            # Refresh tokens
            try:
                result = await self.mcp_client.call_tool(
                    "google-drive-watcher", "refresh_token", {}
                )

                if result.get("success"):
                    console.print("[green]Tokens refreshed successfully[/green]")
                else:
                    console.print(
                        f"[red]Failed to refresh tokens: {result.get('error')}[/red]"
                    )

            except Exception as e:
                console.print(f"[red]Error refreshing tokens: {str(e)}[/red]")

        elif choice == "2":
            # Revoke tokens
            if Confirm.ask("Are you sure you want to revoke OAuth tokens?"):
                try:
                    result = await self.mcp_client.call_tool(
                        "google-drive-watcher", "revoke_token", {}
                    )

                    console.print(
                        "[yellow]Tokens revoked. You'll need to re-authenticate.[/yellow]"
                    )

                except Exception as e:
                    console.print(f"[red]Error revoking tokens: {str(e)}[/red]")

        elif choice == "3":
            # Re-authenticate
            await self._setup_oauth()

        return {"action": choice}

    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        existing_config = {}

        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                existing_config = json.load(f)

        existing_config.update(config)
        existing_config["updated_at"] = datetime.utcnow().isoformat()

        with open(self.config_file, "w") as f:
            json.dump(existing_config, f, indent=2)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}

    async def interactive_setup(self):
        """Run interactive setup wizard"""
        console.print("\n[bold magenta]RAG Watcher Setup Wizard[/bold magenta]\n")

        while True:
            options = [
                "1. Setup Google Drive watcher",
                "2. Configure tenant folders",
                "3. Set sync schedule",
                "4. Check watcher health",
                "5. Manage OAuth tokens",
                "6. Exit",
            ]

            console.print("\n[bold]Select an option:[/bold]")
            for option in options:
                console.print(option)

            choice = Prompt.ask("\nYour choice", choices=["1", "2", "3", "4", "5", "6"])

            if choice == "1":
                await self.setup_google_drive_watcher()
            elif choice == "2":
                await self.setup_tenant_folders()
            elif choice == "3":
                await self.configure_sync_schedule()
            elif choice == "4":
                await self.check_watcher_health()
            elif choice == "5":
                await self.manage_oauth_tokens()
            elif choice == "6":
                console.print("\n[green]Setup complete![/green]")
                break

    async def automated_setup(self, config_file: str):
        """Run automated setup from config file"""
        console.print(
            f"\n[yellow]Running automated setup from {config_file}...[/yellow]"
        )

        try:
            with open(config_file, "r") as f:
                config = json.load(f)

            results = {}

            # Setup watchers
            if "watchers" in config:
                for watcher_type, watcher_config in config["watchers"].items():
                    if watcher_type == "google_drive":
                        results[
                            "google_drive"
                        ] = await self.setup_google_drive_watcher()

            # Setup tenant folders
            if "tenants" in config:
                for tenant in config["tenants"]:
                    if tenant.get("folder_id"):
                        result = await self._add_watch_folder(
                            tenant["id"], tenant["name"], tenant["folder_id"]
                        )
                        results[f"tenant_{tenant['name']}"] = result

            # Configure schedule
            if "sync_interval" in config:
                results["schedule"] = await self.mcp_client.call_tool(
                    "google-drive-watcher",
                    "start_monitoring",
                    {"intervalSeconds": config["sync_interval"]},
                )

            console.print("\n[green]Automated setup complete![/green]")
            return results

        except Exception as e:
            console.print(f"[red]Automated setup failed: {str(e)}[/red]")
            raise


async def main():
    parser = argparse.ArgumentParser(description="RAG Watcher Setup")
    parser.add_argument(
        "--automated", type=str, help="Run automated setup from config file"
    )
    parser.add_argument(
        "--check-health", action="store_true", help="Check watcher health only"
    )
    parser.add_argument(
        "--export-config", type=str, help="Export current configuration"
    )

    args = parser.parse_args()

    setup = RAGWatcherSetup()

    try:
        if args.check_health:
            # Just check health
            health = await setup.check_watcher_health()

            if args.export_config:
                with open(args.export_config, "w") as f:
                    json.dump(health, f, indent=2)
                console.print(
                    f"\n[green]Health status exported to {args.export_config}[/green]"
                )

        elif args.automated:
            # Run automated setup
            await setup.automated_setup(args.automated)

        else:
            # Run interactive setup
            await setup.interactive_setup()

    except Exception as e:
        console.print(f"[red]Setup error: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    asyncio.run(main())
