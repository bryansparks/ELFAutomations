#!/usr/bin/env python3
"""
Enhanced MCP Factory with AgentGateway Integration
This version adds:
1. Automatic AgentGateway registration
2. GitOps artifact generation
3. Dynamic runtime registration capability
"""

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

# Import the original MCP factory classes
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.mcp_factory import ComplexityLevel, MCPConfig
from tools.mcp_factory import MCPFactory as BaseMCPFactory
from tools.mcp_factory import (
    ParameterType,
    ResourceDefinition,
    SchemaBuilder,
    TemplateLibrary,
    ToolDefinition,
    ToolParameter,
)

console = Console()


class EnhancedMCPFactory(BaseMCPFactory):
    """Enhanced MCP Factory with AgentGateway integration"""

    def __init__(self):
        super().__init__()
        self.mcps_dir = self.project_root / "mcps"  # New location for MCPs
        self.agentgateway_url = os.getenv("AGENTGATEWAY_URL", "http://localhost:8080")

    def _generate_mcp(self, config: MCPConfig):
        """Generate MCP with AgentGateway integration"""
        # Call parent implementation
        super()._generate_mcp(config)

        # Generate AgentGateway registration files
        self._generate_agentgateway_registration(config)

        # Generate Kubernetes manifests
        self._generate_kubernetes_manifests(config)

        # Generate GitOps artifacts
        self._generate_gitops_artifacts(config)

        # Optionally register with live AgentGateway
        if Confirm.ask("\nRegister with live AgentGateway now?", default=False):
            self._register_with_agentgateway(config)

        self.console.print(
            f"\n[green]✅ MCP '{config.name}' created with full AgentGateway integration![/green]"
        )
        self._print_next_steps(config)

    def _generate_agentgateway_registration(self, config: MCPConfig):
        """Generate AgentGateway registration files"""
        self.console.print(
            "\n[yellow]📝 Generating AgentGateway registration...[/yellow]"
        )

        # Determine MCP directory based on type and language
        if config.type == "internal":
            if config.language == "typescript":
                mcp_dir = self.mcps_dir / config.name
            else:
                mcp_dir = self.mcps_dir / config.name
        else:
            mcp_dir = self.mcps_dir / "external" / config.name

        mcp_dir.mkdir(parents=True, exist_ok=True)

        # Create manifest.yaml (MCP metadata)
        manifest = {
            "apiVersion": "mcp.elfautomations.com/v1",
            "kind": "MCPServer",
            "metadata": {
                "name": config.name,
                "namespace": "elf-mcps",
                "labels": {
                    "app": config.name,
                    "type": f"{config.type}-mcp",
                    "language": config.language,
                    "complexity": config.complexity.value,
                },
            },
            "spec": {
                "displayName": config.display_name,
                "description": config.description,
                "version": config.version,
                "protocol": "stdio",  # Default, can be http/sse for external
                "runtime": self._get_runtime_config(config),
                "environment": {
                    "required": [
                        k for k, v in config.environment.items() if v.startswith("${")
                    ],
                    "optional": [
                        k
                        for k, v in config.environment.items()
                        if not v.startswith("${")
                    ],
                },
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "category": self._categorize_tool(tool.name),
                    }
                    for tool in config.tools
                ],
                "resources": [
                    {"name": resource.name, "description": resource.description}
                    for resource in config.resources
                ],
                "healthCheck": {
                    "enabled": True,
                    "interval": "30s",
                    "timeout": "5s",
                    "tool": config.tools[0].name if config.tools else "health",
                },
                "rateLimiting": {
                    "enabled": True,
                    "rules": [{"category": "default", "rate": "100/minute"}],
                },
            },
        }

        with open(mcp_dir / "manifest.yaml", "w") as f:
            yaml.dump(manifest, f, default_flow_style=False)

        # Create agentgateway-config.json for runtime registration
        gateway_config = {
            "name": config.name,
            "displayName": config.display_name,
            "description": config.description,
            "protocol": "stdio",
            "runtime": self._get_runtime_config(config),
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": self._tool_to_schema(tool),
                }
                for tool in config.tools
            ],
            "resources": [
                {
                    "name": resource.name,
                    "description": resource.description,
                    "schema": resource.schema,
                }
                for resource in config.resources
            ],
            "categories": self._generate_tool_categories(config.tools),
            "healthCheck": {
                "enabled": True,
                "interval": 30000,  # milliseconds
                "timeout": 5000,
                "tool": config.tools[0].name if config.tools else None,
            },
        }

        with open(mcp_dir / "agentgateway-config.json", "w") as f:
            json.dump(gateway_config, f, indent=2)

        self.console.print(f"  ✅ Created manifest.yaml and agentgateway-config.json")

    def _generate_kubernetes_manifests(self, config: MCPConfig):
        """Generate Kubernetes manifests for the MCP"""
        self.console.print("\n[yellow]🚀 Generating Kubernetes manifests...[/yellow]")

        mcp_dir = self.mcps_dir / config.name
        k8s_dir = mcp_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)

        # Generate ConfigMap with registration label
        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{config.name}-config",
                "namespace": "elf-mcps",
                "labels": {
                    "app": config.name,
                    "agentgateway.elfautomations.com/register": "true",  # Discovery label
                },
            },
            "data": {
                "agentgateway-config.json": json.dumps(
                    json.loads((mcp_dir / "agentgateway-config.json").read_text()),
                    indent=2,
                )
            },
        }

        with open(k8s_dir / "configmap.yaml", "w") as f:
            yaml.dump(configmap, f, default_flow_style=False)

        # Generate Deployment
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": config.name,
                "namespace": "elf-mcps",
                "labels": {"app": config.name},
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": config.name}},
                "template": {
                    "metadata": {"labels": {"app": config.name}},
                    "spec": {
                        "containers": [
                            {
                                "name": config.name,
                                "image": f"elf-automations/{config.name}:latest",
                                "imagePullPolicy": "Never",  # For local development
                                "ports": [{"containerPort": 3000, "name": "mcp"}],
                                "env": [
                                    {"name": k, "value": v}
                                    for k, v in config.environment.items()
                                ],
                                "volumeMounts": [
                                    {
                                        "name": "config",
                                        "mountPath": "/app/config",
                                        "readOnly": True,
                                    }
                                ],
                                "resources": {
                                    "requests": {"memory": "256Mi", "cpu": "100m"},
                                    "limits": {"memory": "512Mi", "cpu": "500m"},
                                },
                                "livenessProbe": {
                                    "httpGet": {"path": "/health", "port": 3000},
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 30,
                                },
                                "readinessProbe": {
                                    "httpGet": {"path": "/ready", "port": 3000},
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 10,
                                },
                            }
                        ],
                        "volumes": [
                            {
                                "name": "config",
                                "configMap": {"name": f"{config.name}-config"},
                            }
                        ],
                    },
                },
            },
        }

        with open(k8s_dir / "deployment.yaml", "w") as f:
            yaml.dump(deployment, f, default_flow_style=False)

        # Generate Service
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": config.name,
                "namespace": "elf-mcps",
                "labels": {"app": config.name},
            },
            "spec": {
                "selector": {"app": config.name},
                "ports": [
                    {"port": 3000, "targetPort": 3000, "protocol": "TCP", "name": "mcp"}
                ],
                "type": "ClusterIP",
            },
        }

        with open(k8s_dir / "service.yaml", "w") as f:
            yaml.dump(service, f, default_flow_style=False)

        # Generate Dockerfile if it doesn't exist
        self._generate_dockerfile(config, mcp_dir)

        self.console.print(f"  ✅ Created Kubernetes manifests in {k8s_dir}")

    def _generate_dockerfile(self, config: MCPConfig, mcp_dir: Path):
        """Generate Dockerfile for the MCP"""
        dockerfile_path = mcp_dir / "Dockerfile"

        if dockerfile_path.exists():
            return

        if config.language == "typescript":
            dockerfile = """FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./
EXPOSE 3000
CMD ["node", "dist/server.js"]
"""
        else:  # Python
            dockerfile = f"""FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["python", "-m", "mcp_servers.{config.name}"]
"""

        with open(dockerfile_path, "w") as f:
            f.write(dockerfile)

        self.console.print("  ✅ Created Dockerfile")

    def _generate_gitops_artifacts(self, config: MCPConfig):
        """Generate GitOps artifacts for the MCP"""
        self.console.print("\n[yellow]📦 Generating GitOps artifacts...[/yellow]")

        # Update the mcps kustomization.yaml
        kustomization_path = self.mcps_dir / "kustomization.yaml"

        if kustomization_path.exists():
            with open(kustomization_path) as f:
                kustomization = yaml.safe_load(f) or {}
        else:
            kustomization = {
                "apiVersion": "kustomize.config.k8s.io/v1beta1",
                "kind": "Kustomization",
            }

        # Add new MCP to resources
        resources = kustomization.get("resources", [])
        mcp_resource = f"{config.name}/k8s/"

        if mcp_resource not in resources:
            resources.append(mcp_resource)
            kustomization["resources"] = sorted(resources)

        with open(kustomization_path, "w") as f:
            yaml.dump(kustomization, f, default_flow_style=False)

        self.console.print(f"  ✅ Updated GitOps kustomization")

    def _register_with_agentgateway(self, config: MCPConfig):
        """Register MCP with live AgentGateway instance"""
        self.console.print("\n[yellow]🔗 Registering with AgentGateway...[/yellow]")

        try:
            # Read the generated config
            mcp_dir = self.mcps_dir / config.name
            with open(mcp_dir / "agentgateway-config.json") as f:
                gateway_config = json.load(f)

            # Call AgentGateway API to register
            response = requests.post(
                f"{self.agentgateway_url}/api/mcp/register",
                json=gateway_config,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code == 200:
                self.console.print(f"  ✅ Successfully registered with AgentGateway")
                result = response.json()
                if "id" in result:
                    self.console.print(f"  📝 MCP ID: {result['id']}")
            else:
                self.console.print(f"  ⚠️  Registration failed: {response.status_code}")
                self.console.print(f"      {response.text}")

        except requests.exceptions.ConnectionError:
            self.console.print("  ⚠️  Could not connect to AgentGateway")
            self.console.print(
                "      MCP will be discovered via ConfigMap labels on deployment"
            )
        except Exception as e:
            self.console.print(f"  ❌ Registration error: {str(e)}")

    def _get_runtime_config(self, config: MCPConfig) -> Dict[str, Any]:
        """Get runtime configuration based on language and type"""
        if config.language == "typescript":
            return {
                "type": "node",
                "command": "node",
                "args": ["dist/server.js"],
                "workingDirectory": "/app",
            }
        else:  # Python
            return {
                "type": "python",
                "command": "python",
                "args": ["-m", f"mcp_servers.{config.name}"],
                "workingDirectory": "/app",
            }

    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool based on name patterns"""
        categories = {
            "auth": ["authenticate", "login", "logout", "token"],
            "data": ["query", "insert", "update", "delete", "fetch"],
            "file": ["read", "write", "list", "upload", "download"],
            "admin": ["configure", "setup", "manage"],
            "monitor": ["health", "status", "metrics", "logs"],
        }

        tool_lower = tool_name.lower()
        for category, patterns in categories.items():
            if any(pattern in tool_lower for pattern in patterns):
                return category

        return "general"

    def _tool_to_schema(self, tool: ToolDefinition) -> Dict[str, Any]:
        """Convert tool definition to JSON schema"""
        properties = {}
        required = []

        for param_name, param in tool.parameters.items():
            properties[param_name] = self._param_to_json_schema(param)
            if param.required:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    def _param_to_json_schema(self, param: ToolParameter) -> Dict[str, Any]:
        """Convert parameter to JSON schema"""
        schema = {"description": param.description}

        if param.type == ParameterType.STRING:
            schema["type"] = "string"
            if param.pattern:
                schema["pattern"] = param.pattern
        elif param.type == ParameterType.NUMBER:
            schema["type"] = "number"
            if param.min_value is not None:
                schema["minimum"] = param.min_value
            if param.max_value is not None:
                schema["maximum"] = param.max_value
        elif param.type == ParameterType.BOOLEAN:
            schema["type"] = "boolean"
        elif param.type == ParameterType.ENUM:
            schema["enum"] = param.enum_values
        elif param.type == ParameterType.OBJECT:
            schema["type"] = "object"
            schema["properties"] = {
                name: self._param_to_json_schema(prop)
                for name, prop in param.properties.items()
            }
        elif param.type == ParameterType.ARRAY:
            schema["type"] = "array"
            if param.items:
                schema["items"] = self._param_to_json_schema(param.items)

        if param.default is not None:
            schema["default"] = param.default

        return schema

    def _generate_tool_categories(self, tools: List[ToolDefinition]) -> Dict[str, Any]:
        """Generate tool categories for the MCP"""
        categories = {}

        for tool in tools:
            category = self._categorize_tool(tool.name)
            if category not in categories:
                categories[category] = {
                    "displayName": category.title(),
                    "description": f"{category.title()} operations",
                    "tools": [],
                }
            categories[category]["tools"].append(tool.name)

        return categories

    def _print_next_steps(self, config: MCPConfig):
        """Print next steps after MCP creation"""
        self.console.print("\n[bold cyan]Next Steps:[/bold cyan]")
        self.console.print(f"\n1. [yellow]Build Docker image:[/yellow]")
        self.console.print(f"   cd mcps/{config.name}")
        self.console.print(f"   docker build -t elf-automations/{config.name}:latest .")

        self.console.print(f"\n2. [yellow]Deploy via GitOps:[/yellow]")
        self.console.print(f"   git add mcps/{config.name}")
        self.console.print(
            f"   git commit -m 'Add {config.name} MCP with AgentGateway integration'"
        )
        self.console.print(f"   git push")

        self.console.print(f"\n3. [yellow]Verify deployment:[/yellow]")
        self.console.print(f"   kubectl get pods -n elf-mcps -l app={config.name}")
        self.console.print(f"   kubectl logs -n elf-mcps -l app={config.name}")

        self.console.print(f"\n4. [yellow]Test via AgentGateway:[/yellow]")
        self.console.print(f"   # From Python:")
        self.console.print(f"   from elf_automations.shared.mcp import MCPClient")
        self.console.print(f"   client = MCPClient()")
        self.console.print(
            f"   result = await client.call_tool('{config.name}', '{config.tools[0].name if config.tools else 'tool_name'}', {{}})"
        )

        self.console.print(
            f"\n[green]The MCP will be automatically discovered by AgentGateway via:[/green]"
        )
        self.console.print(
            f"  • ConfigMap label: agentgateway.elfautomations.com/register=true"
        )
        self.console.print(f"  • Namespace: elf-mcps")
        self.console.print(f"  • Dynamic registration API (if AgentGateway is running)")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced MCP Factory with AgentGateway Integration"
    )
    parser.add_argument("--list", action="store_true", help="List existing MCP servers")
    parser.add_argument("--register", help="Register existing MCP with AgentGateway")

    args = parser.parse_args()

    factory = EnhancedMCPFactory()

    if args.list:
        console.print("[yellow]Listing functionality coming soon![/yellow]")
    elif args.register:
        # TODO: Implement registration of existing MCPs
        console.print(
            f"[yellow]Registering {args.register} with AgentGateway...[/yellow]"
        )
    else:
        factory.create_mcp()


if __name__ == "__main__":
    main()
