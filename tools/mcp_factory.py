#!/usr/bin/env python3
"""
MCP Factory - Unified MCP creation and management tool for ElfAutomations

This tool:
1. Creates internal MCP servers from specifications
2. Integrates external MCP servers from marketplace
3. Generates deployment artifacts for GitOps
4. Registers MCPs with AgentGateway
5. Follows the same patterns as team deployments
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


@dataclass
class MCPConfig:
    """Configuration for an MCP server"""

    name: str
    display_name: str
    description: str
    type: str  # 'internal' or 'external'
    language: str  # 'python' or 'typescript'
    source: str  # package name, repo URL, or 'generated'
    tools: List[Dict[str, Any]]
    resources: List[Dict[str, Any]] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    version: str = "1.0.0"


class MCPFactory:
    """Factory for creating and managing MCP servers"""

    def __init__(self):
        self.console = console
        self.project_root = Path(__file__).parent.parent
        self.mcps_dir = self.project_root / "mcps"
        self.mcps_dir.mkdir(exist_ok=True)

        # MCP types available
        self.INTERNAL_MCPS = {
            "database": "Database operations (read, write, query)",
            "file-system": "File system operations",
            "http-client": "HTTP/REST API client",
            "analytics": "Data analytics tools",
            "monitoring": "System monitoring tools",
            "custom": "Custom tools specific to your business",
        }

        self.EXTERNAL_MCPS = {
            "google-sheets": "Google Sheets integration",
            "slack": "Slack messaging integration",
            "github": "GitHub repository management",
            "jira": "Jira issue tracking",
            "notion": "Notion workspace integration",
            "stripe": "Stripe payment processing",
            "sendgrid": "SendGrid email service",
            "twilio": "Twilio SMS/voice service",
        }

    def create_mcp(self):
        """Main entry point for MCP creation"""
        self.console.print(
            "\n[bold cyan]🔧 MCP Factory - Model Context Protocol Server Creation[/bold cyan]\n"
        )

        # Step 1: Choose MCP type
        mcp_type = self._choose_mcp_type()

        if mcp_type == "internal":
            self._create_internal_mcp()
        else:
            self._integrate_external_mcp()

    def _choose_mcp_type(self) -> str:
        """Choose between internal or external MCP"""
        self.console.print("[bold]What type of MCP do you want to create?[/bold]\n")

        type_table = Table(show_header=True, header_style="bold magenta")
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Description", style="green")
        type_table.add_column("Examples")

        type_table.add_row(
            "Internal",
            "Custom tools for your business",
            "Database ops, Analytics, Monitoring",
        )
        type_table.add_row(
            "External",
            "Third-party service integrations",
            "Google Sheets, Slack, GitHub",
        )

        self.console.print(type_table)

        choice = Prompt.ask(
            "\nChoose type", choices=["internal", "external"], default="internal"
        )

        return choice

    def _create_internal_mcp(self):
        """Create an internal MCP server"""
        self.console.print("\n[bold]Available Internal MCP Types:[/bold]")

        # Show available internal MCPs
        for key, desc in self.INTERNAL_MCPS.items():
            self.console.print(f"  • [cyan]{key}[/cyan]: {desc}")

        mcp_category = Prompt.ask(
            "\nChoose MCP category", choices=list(self.INTERNAL_MCPS.keys())
        )

        # Get MCP details
        name = Prompt.ask("MCP name (e.g., 'analytics-tools')")
        display_name = Prompt.ask(
            "Display name", default=name.replace("-", " ").title()
        )
        description = Prompt.ask("Description")

        # Choose implementation language
        language = Prompt.ask(
            "Implementation language",
            choices=["python", "typescript"],
            default="python",
        )

        # Define tools (simplified for now)
        self.console.print("\n[bold]Define tools for this MCP:[/bold]")
        self.console.print(
            "[dim]Enter tools one by one. Press Enter with empty name to finish.[/dim]"
        )

        tools = []
        while True:
            tool_name = Prompt.ask("\nTool name (or Enter to finish)")
            if not tool_name:
                break

            tool_desc = Prompt.ask("Tool description")
            tools.append(
                {
                    "name": tool_name,
                    "description": tool_desc,
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                }
            )

        # Create MCP configuration
        mcp_config = MCPConfig(
            name=name,
            display_name=display_name,
            description=description,
            type="internal",
            language=language,
            source="generated",
            tools=tools,
        )

        # Generate MCP files
        self._generate_internal_mcp(mcp_config)

    def _integrate_external_mcp(self):
        """Integrate an external MCP server"""
        self.console.print("\n[bold]Available External MCPs:[/bold]")

        # Show available external MCPs
        for key, desc in self.EXTERNAL_MCPS.items():
            self.console.print(f"  • [cyan]{key}[/cyan]: {desc}")

        mcp_choice = Prompt.ask(
            "\nChoose external MCP", choices=list(self.EXTERNAL_MCPS.keys())
        )

        # Get configuration details
        display_name = self.EXTERNAL_MCPS[mcp_choice]

        # Environment variables needed
        self.console.print(f"\n[bold]Configuration for {display_name}:[/bold]")
        env_vars = self._get_env_vars_for_external(mcp_choice)

        environment = {}
        for var in env_vars:
            value = Prompt.ask(f"{var}")
            environment[var] = value

        # Create MCP configuration
        mcp_config = MCPConfig(
            name=mcp_choice,
            display_name=display_name,
            description=f"Integration with {display_name}",
            type="external",
            language="typescript",  # Most external MCPs are TypeScript
            source=f"@modelcontextprotocol/{mcp_choice}",
            tools=[],  # Will be discovered at runtime
            environment=environment,
        )

        # Generate integration files
        self._generate_external_mcp(mcp_config)

    def _generate_internal_mcp(self, config: MCPConfig):
        """Generate files for internal MCP"""
        mcp_dir = self.mcps_dir / config.name
        mcp_dir.mkdir(exist_ok=True)

        self.console.print(
            f"\n[bold yellow]📝 Generating internal MCP: {config.name}[/bold yellow]"
        )

        # Create directory structure
        (mcp_dir / "src").mkdir(exist_ok=True)
        (mcp_dir / "k8s").mkdir(exist_ok=True)

        # Generate source code
        if config.language == "python":
            self._generate_python_mcp(config, mcp_dir)
        else:
            self._generate_typescript_mcp(config, mcp_dir)

        # Generate Dockerfile
        self._generate_mcp_dockerfile(config, mcp_dir)

        # Generate K8s manifests
        self._generate_mcp_k8s_manifests(config, mcp_dir)

        # Generate README
        self._generate_mcp_readme(config, mcp_dir)

        # Update AgentGateway configuration
        self._update_agentgateway_config(config)

        self.console.print(
            f"[green]✅ Internal MCP '{config.name}' created successfully![/green]"
        )
        self.console.print(f"[dim]Location: {mcp_dir}[/dim]")

    def _generate_external_mcp(self, config: MCPConfig):
        """Generate integration files for external MCP"""
        mcp_dir = self.mcps_dir / config.name
        mcp_dir.mkdir(exist_ok=True)

        self.console.print(
            f"\n[bold yellow]📝 Integrating external MCP: {config.name}[/bold yellow]"
        )

        # Create directory structure
        (mcp_dir / "k8s").mkdir(exist_ok=True)

        # Generate wrapper Dockerfile
        self._generate_external_mcp_dockerfile(config, mcp_dir)

        # Generate K8s manifests with environment
        self._generate_mcp_k8s_manifests(config, mcp_dir)

        # Generate integration README
        self._generate_external_mcp_readme(config, mcp_dir)

        # Update AgentGateway configuration
        self._update_agentgateway_config(config)

        self.console.print(
            f"[green]✅ External MCP '{config.name}' integrated successfully![/green]"
        )
        self.console.print(f"[dim]Location: {mcp_dir}[/dim]")

    def _generate_python_mcp(self, config: MCPConfig, mcp_dir: Path):
        """Generate Python MCP server code"""
        server_code = f'''#!/usr/bin/env python3
"""
{config.display_name} - MCP Server
{config.description}
"""

import asyncio
import json
from typing import Any, Dict, List
from mcp import Server, Tool, CallToolResult
from mcp.server.stdio import stdio_server

# Initialize MCP server
app = Server("{config.name}")

# Register tools
'''

        # Add tool implementations
        for tool in config.tools:
            server_code += f'''
@app.call_tool()
async def {tool['name'].replace('-', '_')}(arguments: Dict[str, Any]) -> CallToolResult:
    """
    {tool['description']}
    """
    # TODO: Implement {tool['name']}
    return CallToolResult(
        content=[{{"type": "text", "text": f"Executed {tool['name']}"}}],
        isError=False
    )
'''

        server_code += '''
# List available tools
@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools"""
    return [
'''

        for tool in config.tools:
            server_code += f"""        Tool(
            name="{tool['name']}",
            description="{tool['description']}",
            inputSchema={json.dumps(tool.get('inputSchema', {'type': 'object', 'properties': {}}))}
        ),
"""

        server_code += '''    ]

async def main():
    """Run the MCP server"""
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
'''

        # Write server file
        server_file = mcp_dir / "src" / "server.py"
        with open(server_file, "w") as f:
            f.write(server_code)

        # Generate requirements.txt
        requirements = """mcp>=0.1.0
asyncio
pydantic>=2.0.0
"""

        req_file = mcp_dir / "requirements.txt"
        with open(req_file, "w") as f:
            f.write(requirements)

    def _generate_typescript_mcp(self, config: MCPConfig, mcp_dir: Path):
        """Generate TypeScript MCP server code"""
        # Similar to Python but in TypeScript
        # Omitted for brevity - would follow same pattern
        pass

    def _generate_mcp_dockerfile(self, config: MCPConfig, mcp_dir: Path):
        """Generate Dockerfile for MCP server"""
        if config.language == "python":
            dockerfile = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "src/server.py"]
"""
        else:
            dockerfile = """FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY src/ ./src/

EXPOSE 8080

CMD ["node", "src/server.js"]
"""

        dockerfile_path = mcp_dir / "Dockerfile"
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile)

    def _generate_external_mcp_dockerfile(self, config: MCPConfig, mcp_dir: Path):
        """Generate Dockerfile for external MCP integration"""
        dockerfile = f"""FROM node:20-slim

WORKDIR /app

# Install the external MCP package
RUN npm install -g {config.source}

# Create wrapper script
RUN echo '#!/bin/sh' > /app/start.sh && \\
    echo 'exec npx {config.source}' >> /app/start.sh && \\
    chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]
"""

        dockerfile_path = mcp_dir / "Dockerfile"
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile)

    def _generate_mcp_k8s_manifests(self, config: MCPConfig, mcp_dir: Path):
        """Generate Kubernetes manifests for MCP"""
        k8s_dir = mcp_dir / "k8s"

        # Deployment manifest
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"mcp-{config.name}",
                "namespace": "elf-automations",
                "labels": {
                    "app": f"mcp-{config.name}",
                    "type": "mcp-server",
                    "mcp-type": config.type,
                },
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": f"mcp-{config.name}"}},
                "template": {
                    "metadata": {
                        "labels": {"app": f"mcp-{config.name}", "type": "mcp-server"}
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "mcp-server",
                                "image": f"elf-automations/mcp-{config.name}:latest",
                                "ports": [{"containerPort": 8080, "name": "mcp"}],
                                "env": [],
                            }
                        ]
                    },
                },
            },
        }

        # Add environment variables
        for key, value in config.environment.items():
            deployment["spec"]["template"]["spec"]["containers"][0]["env"].append(
                {
                    "name": key,
                    "valueFrom": {
                        "secretKeyRef": {
                            "name": f"mcp-{config.name}-secrets",
                            "key": key.lower().replace("_", "-"),
                        }
                    },
                }
            )

        # Service manifest
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"mcp-{config.name}-service",
                "namespace": "elf-automations",
                "labels": {"app": f"mcp-{config.name}"},
            },
            "spec": {
                "selector": {"app": f"mcp-{config.name}"},
                "ports": [{"port": 8080, "targetPort": 8080, "name": "mcp"}],
                "type": "ClusterIP",
            },
        }

        # ConfigMap for MCP metadata
        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"mcp-{config.name}-config",
                "namespace": "elf-automations",
            },
            "data": {
                "mcp.json": json.dumps(
                    {
                        "name": config.name,
                        "displayName": config.display_name,
                        "description": config.description,
                        "type": config.type,
                        "version": config.version,
                        "tools": config.tools,
                    },
                    indent=2,
                )
            },
        }

        # Write manifests
        with open(k8s_dir / "deployment.yaml", "w") as f:
            yaml.dump(deployment, f, default_flow_style=False)

        with open(k8s_dir / "service.yaml", "w") as f:
            yaml.dump(service, f, default_flow_style=False)

        with open(k8s_dir / "configmap.yaml", "w") as f:
            yaml.dump(configmap, f, default_flow_style=False)

        # Generate secrets template if environment vars exist
        if config.environment:
            secrets = {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": f"mcp-{config.name}-secrets",
                    "namespace": "elf-automations",
                },
                "stringData": {
                    key.lower().replace("_", "-"): "PLACEHOLDER"
                    for key in config.environment.keys()
                },
            }

            with open(k8s_dir / "secrets-template.yaml", "w") as f:
                yaml.dump(secrets, f, default_flow_style=False)
                f.write(
                    "\n# NOTE: Replace PLACEHOLDER values with actual secrets before applying\n"
                )

    def _generate_mcp_readme(self, config: MCPConfig, mcp_dir: Path):
        """Generate README for internal MCP"""
        readme = f"""# {config.display_name}

## Description
{config.description}

## Type
Internal MCP Server

## Language
{config.language.title()}

## Tools
"""

        for tool in config.tools:
            readme += f"\n### {tool['name']}\n{tool['description']}\n"

        readme += (
            """
## Deployment

### Build Docker Image
```bash
docker build -t elf-automations/mcp-{config.name}:latest .
```

### Deploy to Kubernetes
```bash
kubectl apply -f k8s/
```

## Development

### Local Testing
```bash
"""
            + ("python src/server.py" if config.language == "python" else "npm start")
            + """
```

## Integration
This MCP is automatically registered with AgentGateway and available to all teams.
"""
        )

        readme_file = mcp_dir / "README.md"
        with open(readme_file, "w") as f:
            f.write(readme)

    def _generate_external_mcp_readme(self, config: MCPConfig, mcp_dir: Path):
        """Generate README for external MCP integration"""
        readme = f"""# {config.display_name}

## Description
{config.description}

## Type
External MCP Integration

## Source
{config.source}

## Configuration
The following environment variables are required:
"""

        for key in config.environment.keys():
            readme += f"- `{key}`\n"

        readme += f"""
## Deployment

### Create Secrets
```bash
kubectl create secret generic mcp-{config.name}-secrets \\
    --namespace=elf-automations \\
"""

        for key in config.environment.keys():
            readme += (
                f"    --from-literal={key.lower().replace('_', '-')}=YOUR_VALUE \\\n"
            )

        readme = readme.rstrip(" \\\n") + "\n```"

        readme += """

### Build Docker Image
```bash
docker build -t elf-automations/mcp-{config.name}:latest .
```

### Deploy to Kubernetes
```bash
kubectl apply -f k8s/
```

## Integration
This MCP is automatically registered with AgentGateway and available to all teams.
"""

        readme_file = mcp_dir / "README.md"
        with open(readme_file, "w") as f:
            f.write(readme)

    def _get_env_vars_for_external(self, mcp_type: str) -> List[str]:
        """Get required environment variables for external MCP"""
        env_vars = {
            "google-sheets": [
                "GOOGLE_CLIENT_ID",
                "GOOGLE_CLIENT_SECRET",
                "GOOGLE_REFRESH_TOKEN",
            ],
            "slack": ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"],
            "github": ["GITHUB_TOKEN"],
            "jira": ["JIRA_URL", "JIRA_USERNAME", "JIRA_API_TOKEN"],
            "notion": ["NOTION_API_KEY"],
            "stripe": ["STRIPE_API_KEY"],
            "sendgrid": ["SENDGRID_API_KEY"],
            "twilio": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
        }

        return env_vars.get(mcp_type, [])

    def _update_agentgateway_config(self, config: MCPConfig):
        """Update AgentGateway configuration to include new MCP"""
        agentgateway_config_path = (
            self.project_root / "config" / "agentgateway" / "config.json"
        )

        try:
            # Read existing config
            if agentgateway_config_path.exists():
                with open(agentgateway_config_path) as f:
                    agentgateway_config = json.load(f)
            else:
                agentgateway_config = {"mcpServers": {}}

            # Add new MCP server
            mcp_entry = {
                "uri": f"http://mcp-{config.name}-service:8080",
                "type": config.type,
                "displayName": config.display_name,
                "description": config.description,
            }

            agentgateway_config["mcpServers"][config.name] = mcp_entry

            # Write updated config
            agentgateway_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(agentgateway_config_path, "w") as f:
                json.dump(agentgateway_config, f, indent=2)

            self.console.print(f"[green]✓ Updated AgentGateway configuration[/green]")

        except Exception as e:
            self.console.print(
                f"[yellow]⚠️  Could not update AgentGateway config: {e}[/yellow]"
            )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MCP Factory - Create and manage Model Context Protocol servers"
    )
    parser.add_argument("--list", action="store_true", help="List existing MCP servers")

    args = parser.parse_args()

    factory = MCPFactory()

    if args.list:
        # TODO: Implement listing existing MCPs
        console.print("Listing MCPs not yet implemented")
    else:
        factory.create_mcp()


if __name__ == "__main__":
    main()
