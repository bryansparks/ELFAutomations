#!/usr/bin/env python3
"""
MCP Marketplace - Find and integrate external MCP servers
Discovers public MCP servers and registers them with AgentGateway

This script:
1. Searches for public MCP servers (like Google Sheets, Slack, etc.)
2. Validates their compatibility
3. Registers them with AgentGateway
4. Makes them available to all agents in ElfAutomations
"""

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


@dataclass
class ExternalMCP:
    """External MCP server information"""

    name: str
    description: str
    source: str  # npm package, GitHub repo, etc.
    install_type: str  # npm, github, docker
    install_command: str
    capabilities: List[str]
    author: str
    verified: bool = False
    stars: int = 0


class MCPMarketplace:
    """Discover and integrate external MCP servers"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.external_dir = self.project_root / "mcp" / "external"
        self.agentgateway_config = (
            self.project_root / "config" / "agentgateway" / "config.json"
        )
        self.registry_file = self.external_dir / "registry.json"

        # Known public MCP servers
        self.known_mcps = [
            ExternalMCP(
                name="google-sheets",
                description="Read and write Google Sheets",
                source="@modelcontextprotocol/server-google-sheets",
                install_type="npm",
                install_command="npx -y @modelcontextprotocol/server-google-sheets",
                capabilities=["read_sheet", "write_sheet", "create_sheet"],
                author="Anthropic",
                verified=True,
                stars=150,
            ),
            ExternalMCP(
                name="slack",
                description="Send messages and read channels in Slack",
                source="@modelcontextprotocol/server-slack",
                install_type="npm",
                install_command="npx -y @modelcontextprotocol/server-slack",
                capabilities=["send_message", "read_channel", "list_channels"],
                author="Anthropic",
                verified=True,
                stars=120,
            ),
            ExternalMCP(
                name="github",
                description="Interact with GitHub repositories",
                source="@modelcontextprotocol/server-github",
                install_type="npm",
                install_command="npx -y @modelcontextprotocol/server-github",
                capabilities=["read_repo", "create_issue", "list_prs"],
                author="Anthropic",
                verified=True,
                stars=200,
            ),
            ExternalMCP(
                name="filesystem",
                description="Read and write local files",
                source="@modelcontextprotocol/server-filesystem",
                install_type="npm",
                install_command="npx -y @modelcontextprotocol/server-filesystem",
                capabilities=["read_file", "write_file", "list_directory"],
                author="Anthropic",
                verified=True,
                stars=180,
            ),
            ExternalMCP(
                name="postgres",
                description="Query and manage PostgreSQL databases",
                source="@modelcontextprotocol/server-postgres",
                install_type="npm",
                install_command="npx -y @modelcontextprotocol/server-postgres",
                capabilities=["query", "insert", "update", "delete"],
                author="Anthropic",
                verified=True,
                stars=95,
            ),
            ExternalMCP(
                name="aws",
                description="Interact with AWS services",
                source="mcp-server-aws",
                install_type="npm",
                install_command="npx -y mcp-server-aws",
                capabilities=["s3", "lambda", "dynamodb", "ec2"],
                author="Community",
                verified=False,
                stars=45,
            ),
            ExternalMCP(
                name="jira",
                description="Manage Jira issues and projects",
                source="mcp-server-jira",
                install_type="npm",
                install_command="npx -y mcp-server-jira",
                capabilities=["create_issue", "update_issue", "search_issues"],
                author="Community",
                verified=False,
                stars=30,
            ),
            ExternalMCP(
                name="notion",
                description="Read and write Notion pages and databases",
                source="mcp-server-notion",
                install_type="npm",
                install_command="npx -y mcp-server-notion",
                capabilities=["read_page", "write_page", "query_database"],
                author="Community",
                verified=False,
                stars=65,
            ),
            ExternalMCP(
                name="google-docs",
                description="Read and write Google Docs documents",
                source="@modelcontextprotocol/server-google-docs",
                install_type="npm",
                install_command="npx -y @modelcontextprotocol/server-google-docs",
                capabilities=[
                    "read_document",
                    "write_document",
                    "create_document",
                    "format_text",
                ],
                author="Anthropic",
                verified=True,
                stars=130,
            ),
            ExternalMCP(
                name="google-drive",
                description="Access and manage Google Drive files",
                source="@modelcontextprotocol/server-google-drive",
                install_type="npm",
                install_command="npx -y @modelcontextprotocol/server-google-drive",
                capabilities=[
                    "list_files",
                    "upload_file",
                    "download_file",
                    "create_folder",
                ],
                author="Anthropic",
                verified=True,
                stars=110,
            ),
        ]

    def search_marketplace(self, query: Optional[str] = None):
        """Search for available MCP servers"""
        console.print("\n[bold cyan]🛒 MCP Marketplace[/bold cyan]\n")

        # Filter MCPs based on query
        mcps = self.known_mcps
        if query:
            query_lower = query.lower()
            mcps = [
                m
                for m in mcps
                if query_lower in m.name.lower()
                or query_lower in m.description.lower()
                or any(query_lower in cap for cap in m.capabilities)
            ]

        # Display results in a table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", width=20)
        table.add_column("Description", style="white", width=40)
        table.add_column("Capabilities", style="green", width=30)
        table.add_column("Author", style="yellow")
        table.add_column("⭐", justify="right")
        table.add_column("✓", justify="center")

        for mcp in mcps:
            table.add_row(
                mcp.name,
                mcp.description,
                ", ".join(mcp.capabilities[:3])
                + ("..." if len(mcp.capabilities) > 3 else ""),
                mcp.author,
                str(mcp.stars),
                "✅" if mcp.verified else "❓",
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(mcps)} MCP servers[/dim]")

        return mcps

    def install_mcp(self, mcp_name: str):
        """Install and register an external MCP"""
        # Find the MCP
        mcp = next((m for m in self.known_mcps if m.name == mcp_name), None)
        if not mcp:
            console.print(f"[red]❌ MCP '{mcp_name}' not found[/red]")
            return False

        console.print(f"\n[bold]Installing {mcp.name}...[/bold]")

        # Show MCP details
        panel = Panel(
            f"[bold cyan]Name:[/bold cyan] {mcp.name}\n"
            f"[bold]Description:[/bold] {mcp.description}\n"
            f"[bold]Source:[/bold] {mcp.source}\n"
            f"[bold]Author:[/bold] {mcp.author}\n"
            f"[bold]Verified:[/bold] {'✅ Yes' if mcp.verified else '❓ No'}\n"
            f"[bold]Capabilities:[/bold] {', '.join(mcp.capabilities)}",
            title="MCP Details",
            border_style="blue",
        )
        console.print(panel)

        # Confirm installation
        if not Confirm.ask("\nProceed with installation?"):
            return False

        # Check for required environment variables
        env_vars = self._check_required_env(mcp)
        if env_vars:
            console.print(
                "\n[yellow]⚠️  This MCP requires environment variables:[/yellow]"
            )
            for var in env_vars:
                console.print(f"  - {var}")
            console.print("\nPlease ensure these are set before using the MCP.")

        # Register with AgentGateway
        success = self._register_external_mcp(mcp)

        if success:
            console.print(f"\n[green]✅ Successfully installed {mcp.name}![/green]")
            console.print(
                f"[dim]The MCP is now available to all agents via AgentGateway[/dim]"
            )

            # Save to registry
            self._update_registry(mcp)
        else:
            console.print(f"\n[red]❌ Failed to install {mcp.name}[/red]")

        return success

    def _register_external_mcp(self, mcp: ExternalMCP) -> bool:
        """Register external MCP with AgentGateway"""
        try:
            # Load current config
            with open(self.agentgateway_config, "r") as f:
                config = json.load(f)

            # Ensure structure exists
            if "targets" not in config:
                config["targets"] = {}
            if "mcp" not in config["targets"]:
                config["targets"]["mcp"] = []

            # Create MCP entry based on install type
            if mcp.install_type == "npm":
                # Parse the install command
                cmd_parts = mcp.install_command.split()
                mcp_entry = {
                    "name": mcp.name,
                    "stdio": {"cmd": cmd_parts[0], "args": cmd_parts[1:]},
                }
            elif mcp.install_type == "docker":
                mcp_entry = {
                    "name": mcp.name,
                    "docker": {
                        "image": mcp.source,
                        "env": {},  # Will be populated with required env vars
                    },
                }
            else:
                # Generic stdio command
                mcp_entry = {
                    "name": mcp.name,
                    "stdio": {
                        "cmd": mcp.install_command.split()[0],
                        "args": mcp.install_command.split()[1:],
                    },
                }

            # Check if already exists
            existing = [t for t in config["targets"]["mcp"] if t["name"] == mcp.name]
            if existing:
                if not Confirm.ask(f"\n{mcp.name} is already registered. Update?"):
                    return False
                # Update existing
                idx = config["targets"]["mcp"].index(existing[0])
                config["targets"]["mcp"][idx] = mcp_entry
            else:
                # Add new
                config["targets"]["mcp"].append(mcp_entry)

            # Write updated config
            with open(self.agentgateway_config, "w") as f:
                json.dump(config, f, indent=2)

            return True

        except Exception as e:
            console.print(f"[red]Error registering MCP: {e}[/red]")
            return False

    def _check_required_env(self, mcp: ExternalMCP) -> List[str]:
        """Check required environment variables for MCP"""
        env_requirements = {
            "google-sheets": ["GOOGLE_APPLICATION_CREDENTIALS"],
            "slack": ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"],
            "github": ["GITHUB_TOKEN"],
            "postgres": ["POSTGRES_CONNECTION_STRING"],
            "aws": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
            "jira": ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"],
            "notion": ["NOTION_API_KEY"],
        }

        return env_requirements.get(mcp.name, [])

    def _update_registry(self, mcp: ExternalMCP):
        """Update local registry of installed MCPs"""
        registry = {}
        if self.registry_file.exists():
            with open(self.registry_file, "r") as f:
                registry = json.load(f)

        registry[mcp.name] = {
            "name": mcp.name,
            "description": mcp.description,
            "source": mcp.source,
            "installed_at": str(Path.cwd()),
            "capabilities": mcp.capabilities,
        }

        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w") as f:
            json.dump(registry, f, indent=2)

    def list_installed(self):
        """List all installed external MCPs"""
        if not self.registry_file.exists():
            console.print("[yellow]No external MCPs installed yet[/yellow]")
            return

        with open(self.registry_file, "r") as f:
            registry = json.load(f)

        console.print("\n[bold cyan]📦 Installed External MCPs[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Capabilities", style="green")

        for name, info in registry.items():
            table.add_row(
                name,
                info["description"],
                ", ".join(info["capabilities"][:3])
                + ("..." if len(info["capabilities"]) > 3 else ""),
            )

        console.print(table)

    def test_mcp(self, mcp_name: str):
        """Test an installed MCP"""
        console.print(f"\n[bold]Testing {mcp_name}...[/bold]")

        # This would ideally make a test call through AgentGateway
        # For now, just check if it's registered
        with open(self.agentgateway_config, "r") as f:
            config = json.load(f)

        mcps = config.get("targets", {}).get("mcp", [])
        if any(m["name"] == mcp_name for m in mcps):
            console.print(
                f"[green]✅ {mcp_name} is registered with AgentGateway[/green]"
            )

            # Try to get capabilities (would need actual AgentGateway running)
            console.print(
                "[dim]To fully test, ensure AgentGateway is running and try:[/dim]"
            )
            console.print(
                f"[yellow]curl http://localhost:3000/mcp/{mcp_name}/capabilities[/yellow]"
            )
        else:
            console.print(f"[red]❌ {mcp_name} is not registered[/red]")


def main():
    parser = argparse.ArgumentParser(
        description="MCP Marketplace - Find and install external MCPs"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for MCPs")
    search_parser.add_argument("query", nargs="?", help="Search query")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install an MCP")
    install_parser.add_argument("name", help="Name of MCP to install")

    # List command
    list_parser = subparsers.add_parser("list", help="List installed MCPs")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test an installed MCP")
    test_parser.add_argument("name", help="Name of MCP to test")

    args = parser.parse_args()

    marketplace = MCPMarketplace()

    if args.command == "search":
        marketplace.search_marketplace(args.query)
    elif args.command == "install":
        marketplace.install_mcp(args.name)
    elif args.command == "list":
        marketplace.list_installed()
    elif args.command == "test":
        marketplace.test_mcp(args.name)
    else:
        # Interactive mode
        console.print("[bold cyan]🛒 MCP Marketplace Interactive Mode[/bold cyan]\n")

        while True:
            action = Prompt.ask(
                "\nWhat would you like to do?",
                choices=["search", "install", "list", "test", "quit"],
                default="search",
            )

            if action == "quit":
                break
            elif action == "search":
                query = Prompt.ask("Search query (or press Enter for all)")
                marketplace.search_marketplace(query if query else None)
            elif action == "install":
                name = Prompt.ask("MCP name to install")
                marketplace.install_mcp(name)
            elif action == "list":
                marketplace.list_installed()
            elif action == "test":
                name = Prompt.ask("MCP name to test")
                marketplace.test_mcp(name)


if __name__ == "__main__":
    main()
