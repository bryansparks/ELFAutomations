#!/usr/bin/env python3
"""
Dynamic MCP Registration Script
Allows registration of MCPs with AgentGateway at runtime without redeployment
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


class DynamicMCPRegistrar:
    """Handles dynamic MCP registration with AgentGateway"""

    def __init__(self):
        self.agentgateway_url = self._discover_agentgateway()
        self.headers = self._get_auth_headers()

    def _discover_agentgateway(self) -> str:
        """Discover AgentGateway URL"""
        # Try environment variable first
        if url := os.getenv("AGENTGATEWAY_URL"):
            return url

        # Try common URLs
        urls = [
            "http://agentgateway:8080",
            "http://agentgateway.elf-automations:8080",
            "http://localhost:8080",
        ]

        for url in urls:
            try:
                response = requests.get(f"{url}/health", timeout=2)
                if response.status_code == 200:
                    console.print(f"[green]Found AgentGateway at {url}[/green]")
                    return url
            except:
                continue

        # Ask user
        return Prompt.ask("Enter AgentGateway URL", default="http://localhost:8080")

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {"Content-Type": "application/json"}

        # Check for API key
        if api_key := os.getenv("AGENTGATEWAY_API_KEY"):
            headers["Authorization"] = f"Bearer {api_key}"

        return headers

    def list_registered_mcps(self):
        """List currently registered MCPs"""
        try:
            response = requests.get(
                f"{self.agentgateway_url}/api/mcp/servers",
                headers=self.headers,
                timeout=10,
            )

            if response.status_code == 200:
                servers = response.json()

                table = Table(title="Registered MCP Servers")
                table.add_column("Name", style="cyan")
                table.add_column("Protocol", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Tools", style="blue")

                for server in servers:
                    tools = len(server.get("tools", []))
                    status = (
                        "🟢 Active" if server.get("healthy", False) else "🔴 Inactive"
                    )
                    table.add_row(
                        server["name"],
                        server.get("protocol", "stdio"),
                        status,
                        str(tools),
                    )

                console.print(table)
            else:
                console.print(f"[red]Failed to list MCPs: {response.status_code}[/red]")

        except Exception as e:
            console.print(f"[red]Error listing MCPs: {str(e)}[/red]")

    def register_mcp_from_file(self, config_path: Path):
        """Register MCP from configuration file"""
        if not config_path.exists():
            console.print(f"[red]Configuration file not found: {config_path}[/red]")
            return

        # Load configuration
        with open(config_path) as f:
            if config_path.suffix == ".json":
                config = json.load(f)
            else:
                config = yaml.safe_load(f)

        # Extract MCP config
        if "spec" in config:  # Kubernetes manifest format
            mcp_config = self._convert_manifest_to_config(config)
        else:  # Direct config format
            mcp_config = config

        # Register
        self._register_mcp(mcp_config)

    def register_mcp_interactive(self):
        """Interactive MCP registration"""
        console.print("\n[bold cyan]Interactive MCP Registration[/bold cyan]\n")

        # Basic information
        name = Prompt.ask("MCP name")
        display_name = Prompt.ask(
            "Display name", default=name.replace("-", " ").title()
        )
        description = Prompt.ask("Description")

        # Protocol
        protocol = Prompt.ask(
            "Protocol", choices=["stdio", "http", "sse"], default="stdio"
        )

        # Runtime configuration
        runtime = {}
        if protocol == "stdio":
            runtime["command"] = Prompt.ask("Command (e.g., node, python)")
            args_str = Prompt.ask("Arguments (comma-separated)")
            runtime["args"] = [
                arg.strip() for arg in args_str.split(",") if arg.strip()
            ]
        else:
            runtime["url"] = Prompt.ask("Endpoint URL")

        # Tools
        tools = []
        console.print(
            "\n[yellow]Define tools (press Enter with empty name to finish):[/yellow]"
        )
        while True:
            tool_name = Prompt.ask("\nTool name (or Enter to finish)")
            if not tool_name:
                break

            tool_desc = Prompt.ask("Tool description")
            tools.append({"name": tool_name, "description": tool_desc})

        # Environment variables
        env = {}
        if Confirm.ask("\nDefine environment variables?", default=False):
            console.print(
                "[yellow]Enter variables (press Enter with empty name to finish):[/yellow]"
            )
            while True:
                var_name = Prompt.ask("\nVariable name (or Enter to finish)")
                if not var_name:
                    break

                var_value = Prompt.ask(
                    f"Value for {var_name} (use ${{{var_name}}} for secrets)"
                )
                env[var_name] = var_value

        # Build configuration
        mcp_config = {
            "name": name,
            "displayName": display_name,
            "description": description,
            "protocol": protocol,
            "runtime": {**runtime, "env": env} if env else runtime,
            "tools": tools,
            "healthCheck": {
                "enabled": True,
                "interval": 30000,
                "timeout": 5000,
                "tool": tools[0]["name"] if tools else None,
            },
        }

        # Show configuration
        console.print("\n[bold]Configuration to register:[/bold]")
        console.print(json.dumps(mcp_config, indent=2))

        if Confirm.ask("\nRegister this MCP?", default=True):
            self._register_mcp(mcp_config)

    def _register_mcp(self, config: Dict[str, Any]):
        """Register MCP with AgentGateway"""
        try:
            response = requests.post(
                f"{self.agentgateway_url}/api/mcp/register",
                json=config,
                headers=self.headers,
                timeout=30,
            )

            if response.status_code in [200, 201]:
                result = response.json()
                console.print(
                    f"\n[green]✅ Successfully registered MCP '{config['name']}'[/green]"
                )

                if "id" in result:
                    console.print(f"[cyan]MCP ID: {result['id']}[/cyan]")

                # Test the MCP
                if Confirm.ask("\nTest the MCP now?", default=True):
                    self._test_mcp(config["name"])
            else:
                console.print(
                    f"\n[red]Failed to register MCP: {response.status_code}[/red]"
                )
                console.print(f"[red]{response.text}[/red]")

        except requests.exceptions.ConnectionError:
            console.print("\n[red]Could not connect to AgentGateway[/red]")
            console.print(
                "[yellow]Make sure AgentGateway is running and accessible[/yellow]"
            )
        except Exception as e:
            console.print(f"\n[red]Registration error: {str(e)}[/red]")

    def unregister_mcp(self, name: str):
        """Unregister an MCP"""
        if not Confirm.ask(
            f"Are you sure you want to unregister '{name}'?", default=False
        ):
            return

        try:
            response = requests.delete(
                f"{self.agentgateway_url}/api/mcp/servers/{name}",
                headers=self.headers,
                timeout=10,
            )

            if response.status_code == 200:
                console.print(f"[green]✅ Successfully unregistered '{name}'[/green]")
            else:
                console.print(
                    f"[red]Failed to unregister: {response.status_code}[/red]"
                )

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

    def _test_mcp(self, name: str):
        """Test an MCP by calling its first tool"""
        try:
            # Get MCP details
            response = requests.get(
                f"{self.agentgateway_url}/api/mcp/servers/{name}",
                headers=self.headers,
                timeout=10,
            )

            if response.status_code != 200:
                console.print(f"[red]Could not get MCP details[/red]")
                return

            mcp = response.json()
            tools = mcp.get("tools", [])

            if not tools:
                console.print("[yellow]No tools available to test[/yellow]")
                return

            # Test first tool
            tool = tools[0]
            console.print(f"\n[cyan]Testing tool '{tool['name']}'...[/cyan]")

            response = requests.post(
                f"{self.agentgateway_url}/api/mcp/{name}/tools/{tool['name']}",
                json={},
                headers=self.headers,
                timeout=30,
            )

            if response.status_code == 200:
                console.print("[green]✅ Tool call successful![/green]")
                result = response.json()
                console.print(json.dumps(result, indent=2))
            else:
                console.print(f"[red]Tool call failed: {response.status_code}[/red]")

        except Exception as e:
            console.print(f"[red]Test error: {str(e)}[/red]")

    def _convert_manifest_to_config(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Kubernetes manifest to AgentGateway config"""
        spec = manifest.get("spec", {})

        return {
            "name": manifest["metadata"]["name"],
            "displayName": spec.get("displayName", manifest["metadata"]["name"]),
            "description": spec.get("description", ""),
            "protocol": spec.get("protocol", "stdio"),
            "runtime": spec.get("runtime", {}),
            "tools": spec.get("tools", []),
            "resources": spec.get("resources", []),
            "healthCheck": spec.get(
                "healthCheck", {"enabled": True, "interval": 30000, "timeout": 5000}
            ),
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Dynamic MCP Registration for AgentGateway"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List registered MCPs")

    # Register command
    register_parser = subparsers.add_parser("register", help="Register a new MCP")
    register_parser.add_argument(
        "--file", "-f", type=Path, help="Path to MCP configuration file (JSON or YAML)"
    )
    register_parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive registration"
    )

    # Unregister command
    unregister_parser = subparsers.add_parser("unregister", help="Unregister an MCP")
    unregister_parser.add_argument("name", help="Name of MCP to unregister")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test an MCP")
    test_parser.add_argument("name", help="Name of MCP to test")

    args = parser.parse_args()

    registrar = DynamicMCPRegistrar()

    if args.command == "list":
        registrar.list_registered_mcps()
    elif args.command == "register":
        if args.file:
            registrar.register_mcp_from_file(args.file)
        elif args.interactive:
            registrar.register_mcp_interactive()
        else:
            console.print(
                "[yellow]Use --file or --interactive to register an MCP[/yellow]"
            )
    elif args.command == "unregister":
        registrar.unregister_mcp(args.name)
    elif args.command == "test":
        registrar._test_mcp(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
