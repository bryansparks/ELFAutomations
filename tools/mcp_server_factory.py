#!/usr/bin/env python3
"""
MCP Server Factory - Creates SDK-Compliant MCP Servers
This factory creates MCP Servers that can be called by MCP Clients (like Teams or Claude)
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


@dataclass
class MCPToolSchema:
    """MCP Server tool schema following SDK standards"""

    name: str
    description: str
    inputSchema: Dict[str, Any]  # JSON Schema format

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema,
        }


@dataclass
class MCPResourceSchema:
    """MCP Server resource schema following SDK standards"""

    uri: str
    name: str
    description: str
    mimeType: str = "application/json"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mimeType,
        }


@dataclass
class MCPPromptSchema:
    """MCP Server prompt schema for LLM interactions"""

    name: str
    description: str
    arguments: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
        }


class MCPServerFactory:
    """Factory for creating SDK-compliant MCP Servers"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.servers_dir = self.project_root / "mcp-servers"  # Clear directory name
        self.servers_dir.mkdir(exist_ok=True)
        self.templates = self._load_server_templates()

    def _load_server_templates(self) -> Dict[str, Any]:
        """Load predefined MCP Server templates"""
        return {
            "tool-focused": {
                "name": "Tool-Focused MCP Server",
                "description": "Server that primarily exposes tools for MCP Clients to call",
                "focus": "tools",
                "defaults": {
                    "name": "data-processor",
                    "display_name": "Data Processor",
                    "description": "Processes and analyzes data using various tools",
                },
                "suggested_tools": [
                    {
                        "name": "process_data",
                        "description": "Process raw data and return structured results",
                        "parameters": {
                            "data": {
                                "type": "string",
                                "description": "Raw data to process",
                            },
                            "format": {
                                "type": "string",
                                "description": "Output format",
                                "enum": ["json", "csv", "xml"],
                            },
                        },
                    },
                    {
                        "name": "validate_data",
                        "description": "Validate data against schema",
                        "parameters": {
                            "data": {
                                "type": "object",
                                "description": "Data to validate",
                            },
                            "schema": {
                                "type": "string",
                                "description": "JSON schema for validation",
                            },
                        },
                    },
                ],
            },
            "resource-focused": {
                "name": "Resource-Focused MCP Server",
                "description": "Server that primarily provides access to data resources",
                "focus": "resources",
                "defaults": {
                    "name": "knowledge-base",
                    "display_name": "Knowledge Base",
                    "description": "Provides access to organized knowledge and documentation",
                },
                "suggested_resources": [
                    {
                        "uri": "kb://documents",
                        "name": "documents",
                        "description": "Access to document repository",
                        "mimeType": "application/json",
                    },
                    {
                        "uri": "kb://search",
                        "name": "search-results",
                        "description": "Search results from knowledge base",
                        "mimeType": "application/json",
                    },
                ],
                "suggested_tools": [
                    {
                        "name": "search_knowledge",
                        "description": "Search the knowledge base",
                        "parameters": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {
                                "type": "integer",
                                "description": "Max results",
                                "default": 10,
                            },
                        },
                    }
                ],
            },
            "prompt-focused": {
                "name": "Prompt-Focused MCP Server",
                "description": "Server that primarily provides prompts to enhance LLM interactions",
                "focus": "prompts",
                "defaults": {
                    "name": "prompt-templates",
                    "display_name": "Prompt Templates",
                    "description": "Provides structured prompts for various tasks",
                },
                "suggested_prompts": [
                    {
                        "name": "code_review",
                        "description": "Generate code review prompts",
                        "arguments": [
                            {
                                "name": "language",
                                "description": "Programming language",
                                "required": True,
                            },
                            {
                                "name": "complexity",
                                "description": "Code complexity level",
                                "required": False,
                            },
                        ],
                    },
                    {
                        "name": "documentation",
                        "description": "Generate documentation prompts",
                        "arguments": [
                            {
                                "name": "topic",
                                "description": "Documentation topic",
                                "required": True,
                            },
                            {
                                "name": "audience",
                                "description": "Target audience",
                                "required": False,
                            },
                        ],
                    },
                ],
                "suggested_tools": [
                    {
                        "name": "customize_prompt",
                        "description": "Customize prompt templates",
                        "parameters": {
                            "template": {
                                "type": "string",
                                "description": "Template name",
                            },
                            "variables": {
                                "type": "object",
                                "description": "Template variables",
                            },
                        },
                    }
                ],
            },
            "balanced": {
                "name": "Balanced MCP Server",
                "description": "Server that provides a mix of tools, resources, and prompts",
                "focus": "balanced",
                "defaults": {
                    "name": "multi-service",
                    "display_name": "Multi Service",
                    "description": "Provides comprehensive tools, resources, and prompts",
                },
                "suggested_tools": [
                    {
                        "name": "health_check",
                        "description": "Check server health and status",
                        "parameters": {},
                    }
                ],
                "suggested_resources": [
                    {
                        "uri": "service://status",
                        "name": "status",
                        "description": "Service status information",
                        "mimeType": "application/json",
                    }
                ],
                "suggested_prompts": [
                    {
                        "name": "help",
                        "description": "Get help with using this server",
                        "arguments": [
                            {
                                "name": "topic",
                                "description": "Help topic",
                                "required": False,
                            }
                        ],
                    }
                ],
            },
            "api-facade": {
                "name": "API Facade MCP Server",
                "description": "Intelligent wrapper for external APIs with high-level operations",
                "focus": "api-facade",
                "defaults": {
                    "name": "api-gateway",
                    "display_name": "API Gateway",
                    "description": "Smart facade for external API services",
                },
                "requires_api_docs": True,
                "requires_api_key": True,
                "suggested_tools": [
                    {
                        "name": "query_api",
                        "description": "Execute high-level queries against the external API",
                        "parameters": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query to execute",
                            },
                            "context": {
                                "type": "object",
                                "description": "Additional context for the query",
                                "required": False,
                            },
                        },
                    },
                    {
                        "name": "search_capabilities",
                        "description": "Search available API capabilities and endpoints",
                        "parameters": {
                            "search_term": {
                                "type": "string",
                                "description": "Term to search for in API capabilities",
                            }
                        },
                    },
                    {
                        "name": "get_api_schema",
                        "description": "Get schema information for specific API endpoints",
                        "parameters": {
                            "endpoint": {
                                "type": "string",
                                "description": "API endpoint to get schema for",
                            }
                        },
                    },
                ],
                "suggested_resources": [
                    {
                        "uri": "api://documentation",
                        "name": "api-docs",
                        "description": "Processed API documentation and schemas",
                        "mimeType": "application/json",
                    },
                    {
                        "uri": "api://endpoints",
                        "name": "endpoints",
                        "description": "Available API endpoints and their capabilities",
                        "mimeType": "application/json",
                    },
                ],
            },
            "custom": {
                "name": "Custom MCP Server",
                "description": "Start from scratch with no predefined suggestions",
                "focus": "custom",
                "defaults": {
                    "name": "custom-server",
                    "display_name": "Custom Server",
                    "description": "Custom MCP Server implementation",
                },
            },
        }

    def _select_server_template(self) -> Dict[str, Any]:
        """Interactive template selection"""
        console.print("\n[bold]Choose a Server Template:[/bold]")
        console.print("[dim]Templates provide starter suggestions and defaults[/dim]\n")

        # Show template options
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Option", style="cyan", width=12)
        table.add_column("Template", style="green", width=25)
        table.add_column("Description", style="white", width=50)

        options = list(self.templates.keys())
        for i, key in enumerate(options, 1):
            template = self.templates[key]
            table.add_row(f"{i}", template["name"], template["description"])

        console.print(table)

        # Get user choice
        while True:
            choice = Prompt.ask(
                "\nSelect template",
                choices=[str(i) for i in range(1, len(options) + 1)],
                default="1",
            )

            try:
                selected_key = options[int(choice) - 1]
                selected_template = self.templates[selected_key]

                console.print(
                    f"\n[green]✓ Selected: {selected_template['name']}[/green]"
                )
                if selected_template["focus"] != "custom":
                    console.print(
                        f"[dim]This template focuses on: {selected_template['focus']}[/dim]"
                    )

                return selected_template
            except (ValueError, IndexError):
                console.print("[red]Invalid choice. Please try again.[/red]")

    def create_mcp_server(self):
        """Interactive MCP Server creation following SDK patterns"""
        console.print("\n[bold cyan]🔧 MCP Server Factory[/bold cyan]")
        console.print(
            "[yellow]Create MCP Servers that expose tools, resources, and prompts[/yellow]"
        )
        console.print(
            "[dim]MCP Clients (like Teams or Claude) will connect to these servers[/dim]\n"
        )

        # Server template selection
        template = self._select_server_template()

        # Server type
        server_type = Prompt.ask(
            "Server type", choices=["internal", "external"], default="internal"
        )

        if server_type == "external":
            console.print(
                "\n[yellow]Note: This creates a wrapper for an external MCP Server[/yellow]"
            )
            console.print(
                "[dim]The wrapper handles authentication and routing to the external server[/dim]\n"
            )

        # Basic info with template defaults
        name = Prompt.ask(
            "MCP Server name (kebab-case)", default=template["defaults"]["name"]
        )
        display_name = Prompt.ask(
            "Display name", default=template["defaults"]["display_name"]
        )
        description = Prompt.ask(
            "Description of what this server provides",
            default=template["defaults"]["description"],
        )

        # Special handling for API Facade template
        api_config = {}
        if template.get("requires_api_docs", False):
            console.print(f"\n[yellow]API Facade Configuration:[/yellow]")
            console.print(
                "[dim]This template creates an intelligent wrapper for external APIs[/dim]"
            )

            api_config["docs_url"] = Prompt.ask(
                "API Documentation URL (OpenAPI/Swagger JSON or docs page)",
                default="https://www.familysearch.org/developers/docs/api/swagger.json",
            )

            api_config["base_url"] = Prompt.ask(
                "API Base URL", default="https://api.familysearch.org"
            )

            if template.get("requires_api_key", False):
                api_config["requires_api_key"] = Confirm.ask(
                    "Does this API require an API key?", default=True
                )
                if api_config["requires_api_key"]:
                    api_config["api_key_name"] = Prompt.ask(
                        "API Key parameter name", default="X-API-Key"
                    )
                    api_config["api_key_type"] = Prompt.ask(
                        "API Key type",
                        choices=["header", "query", "bearer"],
                        default="header",
                    )

            # Update defaults based on API
            if "familysearch" in api_config["docs_url"].lower():
                name = Prompt.ask(
                    "MCP Server name (kebab-case)", default="familysearch-api"
                )
                display_name = Prompt.ask(
                    "Display name", default="FamilySearch API Gateway"
                )
                description = Prompt.ask(
                    "Description",
                    default="Intelligent wrapper for FamilySearch genealogy APIs",
                )

        # Implementation language
        language = Prompt.ask(
            "Implementation language",
            choices=["typescript", "python"],
            default="typescript",
        )

        # Transport type
        transport = Prompt.ask(
            "Transport type", choices=["stdio", "http", "sse"], default="http"
        )

        console.print(f"\n[cyan]Creating MCP Server: {display_name}[/cyan]")
        console.print(
            f"[dim]This server will expose tools that MCP Clients can use[/dim]\n"
        )

        # Define tools following SDK patterns
        tools = self._define_server_tools(template)

        # Define resources (optional)
        resources = []
        default_resources = template["focus"] in ["resources", "balanced"]
        if Confirm.ask(
            "\nDoes this server expose resources?", default=default_resources
        ):
            resources = self._define_server_resources(template)

        # Define prompts (optional)
        prompts = []
        default_prompts = template["focus"] in ["prompts", "balanced"]
        if Confirm.ask("\nDoes this server provide prompts?", default=default_prompts):
            prompts = self._define_server_prompts(template)

        # Generate the MCP Server
        self._generate_mcp_server(
            name=name,
            display_name=display_name,
            description=description,
            language=language,
            transport=transport,
            server_type=server_type,
            tools=tools,
            resources=resources,
            prompts=prompts,
            template=template,
            api_config=api_config,
        )

        console.print(f"\n[green]✅ MCP Server '{name}' created successfully![/green]")
        console.print(
            f"[dim]This server can now be used by MCP Clients through AgentGateway[/dim]"
        )
        self._print_next_steps(name, language, server_type)

    def _define_server_tools(self, template: Dict[str, Any]) -> List[MCPToolSchema]:
        """Define tools that this server will expose"""
        tools = []

        console.print("\n[bold]Define Tools This Server Will Expose:[/bold]")
        console.print("[dim]These tools can be called by MCP Clients[/dim]")

        # Show template suggestions if available
        if "suggested_tools" in template and template["suggested_tools"]:
            console.print(
                f"\n[yellow]Template suggestions for {template['name']}:[/yellow]"
            )
            for i, tool in enumerate(template["suggested_tools"], 1):
                console.print(
                    f"  {i}. [cyan]{tool['name']}[/cyan] - {tool['description']}"
                )

            if Confirm.ask(
                "\nWould you like to start with template suggestions?", default=True
            ):
                for tool_template in template["suggested_tools"]:
                    if Confirm.ask(
                        f"\nAdd suggested tool '{tool_template['name']}'?", default=True
                    ):
                        # Convert template format to proper JSON Schema
                        input_schema = {
                            "type": "object",
                            "properties": {},
                            "required": [],
                            "additionalProperties": False,
                        }

                        if "parameters" in tool_template:
                            for param_name, param_def in tool_template[
                                "parameters"
                            ].items():
                                input_schema["properties"][param_name] = param_def
                                if param_def.get("required", True):
                                    input_schema["required"].append(param_name)

                        tools.append(
                            MCPToolSchema(
                                name=tool_template["name"],
                                description=tool_template["description"],
                                inputSchema=input_schema,
                            )
                        )
                        console.print(
                            f"[green]✓ Added template tool '{tool_template['name']}'[/green]"
                        )

        # Allow custom tools
        if tools:
            console.print(f"\n[bold]Add Additional Custom Tools (Optional):[/bold]")
            console.print(
                f"[dim]You already have {len(tools)} tools from the template. Add more if needed.[/dim]"
            )
        else:
            console.print(f"\n[bold]Add Custom Tools:[/bold]")
            console.print(
                f"[dim]Define the tools this server will provide to MCP Clients.[/dim]"
            )

        if not Confirm.ask("\nWould you like to add custom tools?", default=False):
            return tools

        while True:
            name = Prompt.ask(
                "\nTool name (snake_case, or Enter to finish)", default=""
            )
            if not name.strip():
                break

            description = Prompt.ask("What does this tool do")

            # Build JSON Schema for parameters
            console.print(
                f"\n[yellow]Define parameters for tool '{name}' (optional):[/yellow]"
            )
            properties = {}
            required = []

            if not Confirm.ask("Does this tool need parameters?", default=True):
                properties = {}
                required = []
            else:
                while True:
                    param_name = Prompt.ask(
                        "Parameter name (or Enter to finish)", default=""
                    )
                    if not param_name.strip():
                        break

                param_type = Prompt.ask(
                    "Parameter type",
                    choices=[
                        "string",
                        "number",
                        "integer",
                        "boolean",
                        "object",
                        "array",
                    ],
                    default="string",
                )

                param_desc = Prompt.ask("Parameter description")

                # Build parameter schema
                param_schema = {"type": param_type, "description": param_desc}

                # Add constraints based on type
                if param_type == "string":
                    if Confirm.ask("Add pattern constraint?", default=False):
                        param_schema["pattern"] = Prompt.ask("Regex pattern")
                    if Confirm.ask("Add enum constraint?", default=False):
                        values = Prompt.ask("Enum values (comma-separated)")
                        param_schema["enum"] = [v.strip() for v in values.split(",")]
                elif param_type in ["number", "integer"]:
                    if Confirm.ask("Add min/max constraints?", default=False):
                        param_schema["minimum"] = float(Prompt.ask("Minimum value"))
                        param_schema["maximum"] = float(Prompt.ask("Maximum value"))

                properties[param_name] = param_schema

                if Confirm.ask(f"Is '{param_name}' required?", default=True):
                    required.append(param_name)

            # Create proper JSON Schema
            input_schema = {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            }

            tools.append(
                MCPToolSchema(
                    name=name, description=description, inputSchema=input_schema
                )
            )

            console.print(f"[green]✓ Added tool '{name}' to server[/green]")

        console.print(
            f"\n[cyan]📋 Tools Summary: {len(tools)} tools defined for this server[/cyan]"
        )
        for tool in tools:
            console.print(f"  • {tool.name} - {tool.description}")

        return tools

    def _define_server_resources(
        self, template: Dict[str, Any]
    ) -> List[MCPResourceSchema]:
        """Define resources that this server will expose"""
        resources = []

        console.print("\n[bold]Define Resources This Server Will Expose:[/bold]")
        console.print("[dim]Resources are data that MCP Clients can read[/dim]")

        # Show template suggestions if available
        if "suggested_resources" in template and template["suggested_resources"]:
            console.print(
                f"\n[yellow]Template suggestions for {template['name']}:[/yellow]"
            )
            for i, resource in enumerate(template["suggested_resources"], 1):
                console.print(
                    f"  {i}. [cyan]{resource['name']}[/cyan] - {resource['description']}"
                )

            if Confirm.ask(
                "\nWould you like to start with template suggestions?", default=True
            ):
                for resource_template in template["suggested_resources"]:
                    if Confirm.ask(
                        f"\nAdd suggested resource '{resource_template['name']}'?",
                        default=True,
                    ):
                        resources.append(
                            MCPResourceSchema(
                                uri=resource_template["uri"],
                                name=resource_template["name"],
                                description=resource_template["description"],
                                mimeType=resource_template.get(
                                    "mimeType", "application/json"
                                ),
                            )
                        )
                        console.print(
                            f"[green]✓ Added template resource '{resource_template['name']}'[/green]"
                        )

        # Allow custom resources
        if resources:
            console.print(f"\n[bold]Add Additional Custom Resources (Optional):[/bold]")
            console.print(
                f"[dim]You already have {len(resources)} resources from the template. Add more if needed.[/dim]"
            )
        else:
            console.print(f"\n[bold]Add Custom Resources:[/bold]")
            console.print(
                f"[dim]Define the resources this server will provide to MCP Clients.[/dim]"
            )

        if not Confirm.ask("\nWould you like to add custom resources?", default=False):
            return resources

        while True:
            name = Prompt.ask("\nResource name (or Enter to finish)", default="")
            if not name.strip():
                break

            uri = Prompt.ask(
                "Resource URI (e.g., 'config://settings')", default=f"{name}://default"
            )
            description = Prompt.ask("What data does this resource provide")
            mime_type = Prompt.ask("MIME type", default="application/json")

            resources.append(
                MCPResourceSchema(
                    uri=uri, name=name, description=description, mimeType=mime_type
                )
            )

            console.print(f"[green]✓ Added resource '{name}' to server[/green]")

        if resources:
            console.print(
                f"\n[cyan]📂 Resources Summary: {len(resources)} resources defined for this server[/cyan]"
            )
            for resource in resources:
                console.print(
                    f"  • {resource.name} ({resource.uri}) - {resource.description}"
                )

        return resources

    def _define_server_prompts(self, template: Dict[str, Any]) -> List[MCPPromptSchema]:
        """Define prompts that this server will provide"""
        prompts = []

        console.print("\n[bold]Define Prompts This Server Will Provide:[/bold]")
        console.print("[dim]Prompts help MCP Clients interact with LLMs[/dim]")

        # Show template suggestions if available
        if "suggested_prompts" in template and template["suggested_prompts"]:
            console.print(
                f"\n[yellow]Template suggestions for {template['name']}:[/yellow]"
            )
            for i, prompt in enumerate(template["suggested_prompts"], 1):
                console.print(
                    f"  {i}. [cyan]{prompt['name']}[/cyan] - {prompt['description']}"
                )

            if Confirm.ask(
                "\nWould you like to start with template suggestions?", default=True
            ):
                for prompt_template in template["suggested_prompts"]:
                    if Confirm.ask(
                        f"\nAdd suggested prompt '{prompt_template['name']}'?",
                        default=True,
                    ):
                        prompts.append(
                            MCPPromptSchema(
                                name=prompt_template["name"],
                                description=prompt_template["description"],
                                arguments=prompt_template.get("arguments", []),
                            )
                        )
                        console.print(
                            f"[green]✓ Added template prompt '{prompt_template['name']}'[/green]"
                        )

        # Allow custom prompts
        if prompts:
            console.print(f"\n[bold]Add Additional Custom Prompts (Optional):[/bold]")
            console.print(
                f"[dim]You already have {len(prompts)} prompts from the template. Add more if needed.[/dim]"
            )
        else:
            console.print(f"\n[bold]Add Custom Prompts:[/bold]")
            console.print(
                f"[dim]Define the prompts this server will provide to MCP Clients.[/dim]"
            )

        if not Confirm.ask("\nWould you like to add custom prompts?", default=False):
            return prompts

        while True:
            name = Prompt.ask("\nPrompt name (or Enter to finish)", default="")
            if not name.strip():
                break

            description = Prompt.ask("What does this prompt help with")

            # Define prompt arguments
            arguments = []
            console.print(
                f"\n[yellow]Define arguments for prompt '{name}' (optional):[/yellow]"
            )

            if not Confirm.ask("Does this prompt need arguments?", default=False):
                arguments = []
            else:
                while True:
                    arg_name = Prompt.ask(
                        "Argument name (or Enter to finish)", default=""
                    )
                    if not arg_name.strip():
                        break

                arg_desc = Prompt.ask("Argument description")
                arg_required = Confirm.ask("Is this argument required?", default=True)

                arguments.append(
                    {
                        "name": arg_name,
                        "description": arg_desc,
                        "required": arg_required,
                    }
                )

            prompts.append(
                MCPPromptSchema(name=name, description=description, arguments=arguments)
            )

            console.print(f"[green]✓ Added prompt '{name}' to server[/green]")

        if prompts:
            console.print(
                f"\n[cyan]💬 Prompts Summary: {len(prompts)} prompts defined for this server[/cyan]"
            )
            for prompt in prompts:
                args_count = len(prompt.arguments) if prompt.arguments else 0
                console.print(
                    f"  • {prompt.name} ({args_count} args) - {prompt.description}"
                )

        return prompts

    def _generate_mcp_server(
        self,
        name: str,
        display_name: str,
        description: str,
        language: str,
        transport: str,
        server_type: str,
        tools: List[MCPToolSchema],
        resources: List[MCPResourceSchema],
        prompts: List[MCPPromptSchema],
        template: Dict[str, Any],
        api_config: Dict[str, Any] = None,
    ):
        """Generate MCP Server following SDK patterns"""
        server_dir = self.servers_dir / name
        server_dir.mkdir(parents=True, exist_ok=True)

        # Generate server metadata
        metadata = {
            "type": "mcp-server",
            "server_type": server_type,
            "name": name,
            "displayName": display_name,
            "description": description,
            "language": language,
            "transport": transport,
            "template": template.get("focus", "custom"),
            "exposes": {
                "tools": len(tools),
                "resources": len(resources),
                "prompts": len(prompts),
            },
        }

        # Add API facade configuration
        if api_config:
            metadata["api_config"] = {
                "docs_url": api_config.get("docs_url"),
                "base_url": api_config.get("base_url"),
                "requires_api_key": api_config.get("requires_api_key", False),
                "api_key_name": api_config.get("api_key_name"),
                "api_key_type": api_config.get("api_key_type"),
            }

        with open(server_dir / "mcp-server.json", "w") as f:
            json.dump(metadata, f, indent=2)

        if language == "typescript":
            self._generate_typescript_mcp_server(
                server_dir,
                name,
                display_name,
                description,
                transport,
                server_type,
                tools,
                resources,
                prompts,
                template,
                api_config,
            )
        else:
            self._generate_python_mcp_server(
                server_dir,
                name,
                display_name,
                description,
                transport,
                server_type,
                tools,
                resources,
                prompts,
                template,
                api_config,
            )

        # Generate common files
        self._generate_server_manifest(
            server_dir,
            name,
            display_name,
            description,
            language,
            transport,
            tools,
            resources,
            prompts,
        )
        self._generate_server_readme(
            server_dir,
            name,
            display_name,
            description,
            server_type,
            tools,
            resources,
            prompts,
        )
        self._generate_agentgateway_config(
            server_dir, name, display_name, description, transport, tools, resources
        )
        self._generate_kubernetes_manifests(server_dir, name, display_name, language)

    def _generate_typescript_mcp_server(
        self,
        server_dir: Path,
        name: str,
        display_name: str,
        description: str,
        transport: str,
        server_type: str,
        tools: List[MCPToolSchema],
        resources: List[MCPResourceSchema],
        prompts: List[MCPPromptSchema],
        template: Dict[str, Any],
        api_config: Dict[str, Any] = None,
    ):
        """Generate TypeScript MCP Server"""

        # Create src directory
        src_dir = server_dir / "src"
        src_dir.mkdir(exist_ok=True)

        # Add API facade specific imports
        api_imports = ""
        if template.get("focus") == "api-facade" and api_config:
            api_imports = """
import axios, { AxiosInstance } from "axios";
import { load } from "js-yaml";"""

        # Generate server.ts
        server_code = f"""/**
 * {display_name} - MCP Server
 * {description}
 *
 * This is an MCP Server that exposes tools, resources, and prompts
 * to MCP Clients (like Teams or Claude) via the Model Context Protocol.
 */

import {{ Server }} from "@modelcontextprotocol/sdk/server/index.js";
import {{ StdioServerTransport }} from "@modelcontextprotocol/sdk/server/stdio.js";
import {{
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
  ReadResourceRequestSchema,
  McpError,
  Tool,
  Resource,
  Prompt,
}} from "@modelcontextprotocol/sdk/types.js";
import {{ z }} from "zod";{api_imports}

console.error("[{display_name}] Starting MCP Server...");

{self._generate_api_facade_constants(api_config) if template.get("focus") == "api-facade" else ""}

// Tool schemas for parameter validation
{self._generate_zod_schemas(tools)}

// Tools exposed by this server
const TOOLS: Tool[] = {json.dumps([t.to_dict() for t in tools], indent=2)};

// Resources exposed by this server
const RESOURCES: Resource[] = {json.dumps([r.to_dict() for r in resources], indent=2)};

// Prompts provided by this server
const PROMPTS: Prompt[] = {json.dumps([p.to_dict() for p in prompts], indent=2)};

/**
 * {display_name} MCP Server
 * This server can be used by any MCP Client through the Model Context Protocol
 */
class {self._to_class_name(name)}Server {{
  private server: Server;{self._generate_api_facade_properties(api_config) if template.get("focus") == "api-facade" else ""}

  constructor() {{
    console.error("[{display_name}] Initializing server...");

    this.server = new Server(
      {{
        name: "{name}",
        version: "1.0.0",
      }},
      {{
        capabilities: {{
          tools: {json.dumps({"listChanged": True}) if tools else "{}"},
          resources: {json.dumps({"subscribe": True, "listChanged": True}) if resources else "{}"},
          prompts: {json.dumps({"listChanged": True}) if prompts else "{}"},
        }},
      }}
    );{self._generate_api_facade_constructor_init(api_config) if template.get("focus") == "api-facade" else ""}

    this.setupHandlers();
    console.error("[{display_name}] Server initialized successfully");
  }}

  private setupHandlers() {{
    // Register tool handlers
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {{
      console.error("[{display_name}] Client requested tool list");
      return {{ tools: TOOLS }};
    }});

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {{
      const {{ name: toolName, arguments: args }} = request.params;
      console.error(`[{display_name}] Client calling tool: ${{toolName}}`);

      try {{
        switch (toolName) {{
{self._generate_tool_switch_cases(tools)}
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${{toolName}}`
            );
        }}
      }} catch (error) {{
        if (error instanceof z.ZodError) {{
          throw new McpError(
            ErrorCode.InvalidParams,
            `Invalid parameters: ${{error.message}}`
          );
        }}
        throw error;
      }}
    }});

    // Register resource handlers
    if (RESOURCES.length > 0) {{
      this.server.setRequestHandler(ListResourcesRequestSchema, async () => {{
        console.error("[{display_name}] Client requested resource list");
        return {{ resources: RESOURCES }};
      }});

      this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {{
        const {{ uri }} = request.params;
        console.error(`[{display_name}] Client reading resource: ${{uri}}`);

        const resource = RESOURCES.find((r) => r.uri === uri);
        if (!resource) {{
          throw new McpError(
            ErrorCode.InvalidParams,
            `Unknown resource: ${{uri}}`
          );
        }}

        return {{
          contents: [
            {{
              uri,
              mimeType: resource.mimeType,
              text: await this.readResource(uri),
            }},
          ],
        }};
      }});
    }}

    // Register prompt handlers
    if (PROMPTS.length > 0) {{
      this.server.setRequestHandler(ListPromptsRequestSchema, async () => {{
        console.error("[{display_name}] Client requested prompt list");
        return {{ prompts: PROMPTS }};
      }});

      this.server.setRequestHandler(GetPromptRequestSchema, async (request) => {{
        const {{ name, arguments: args }} = request.params;
        console.error(`[{display_name}] Client getting prompt: ${{name}}`);

        const prompt = PROMPTS.find((p) => p.name === name);
        if (!prompt) {{
          throw new McpError(
            ErrorCode.InvalidParams,
            `Unknown prompt: ${{name}}`
          );
        }}

        return {{
          description: prompt.description,
          messages: await this.getPromptMessages(name, args),
        }};
      }});
    }}
  }}

{self._generate_tool_implementations(tools, server_type)}

  private async readResource(uri: string): Promise<string> {{
    console.error(`[{display_name}] Reading resource: ${{uri}}`);
    // TODO: Implement resource reading logic
    return JSON.stringify({{
      message: "Resource content for " + uri,
      timestamp: new Date().toISOString()
    }});
  }}

  private async getPromptMessages(name: string, args?: Record<string, string>): Promise<any[]> {{
    console.error(`[{display_name}] Generating prompt: ${{name}}`);
    // TODO: Implement prompt generation logic
    return [
      {{
        role: "user",
        content: {{
          type: "text",
          text: `Prompt ${{name}} with args: ${{JSON.stringify(args)}}`,
        }},
      }},
    ];
  }}{self._generate_api_facade_methods(api_config) if template.get("focus") == "api-facade" else ""}

  async run() {{
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("[{display_name}] MCP Server running - ready for client connections");
  }}
}}

// Start the MCP Server
const server = new {self._to_class_name(name)}Server();
server.run().catch((error) => {{
  console.error("[{display_name}] Server error:", error);
  process.exit(1);
}});
"""

        with open(src_dir / "server.ts", "w") as f:
            f.write(server_code)

        # Generate package.json
        package_json = {
            "name": f"@elf-automations/{name}-mcp-server",
            "version": "1.0.0",
            "description": f"{description} (MCP Server)",
            "type": "module",
            "main": "dist/server.js",
            "scripts": {
                "build": "tsc",
                "start": "node dist/server.js",
                "dev": "tsx src/server.ts",
                "test": "jest",
                "lint": "eslint src/",
            },
            "dependencies": {"@modelcontextprotocol/sdk": "^0.5.0", "zod": "^3.23.8"},
            "devDependencies": {
                "@types/node": "^20.10.5",
                "tsx": "^4.7.0",
                "typescript": "^5.3.3",
                "jest": "^29.7.0",
                "@typescript-eslint/eslint-plugin": "^6.0.0",
                "@typescript-eslint/parser": "^6.0.0",
                "eslint": "^8.44.0",
            },
        }

        # Add external dependencies if it's an external wrapper or API facade
        if server_type == "external" or template.get("focus") == "api-facade":
            package_json["dependencies"]["axios"] = "^1.6.0"
            package_json["devDependencies"]["@types/axios"] = "^0.14.0"

        # Add YAML parsing for API facade servers
        if template.get("focus") == "api-facade":
            package_json["dependencies"]["js-yaml"] = "^4.1.0"
            package_json["devDependencies"]["@types/js-yaml"] = "^4.0.5"

        with open(server_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)

        # Generate tsconfig.json
        self._generate_tsconfig(server_dir)

        # Generate .gitignore
        self._generate_gitignore(server_dir)

    def _generate_python_mcp_server(
        self,
        server_dir: Path,
        name: str,
        display_name: str,
        description: str,
        transport: str,
        server_type: str,
        tools: List[MCPToolSchema],
        resources: List[MCPResourceSchema],
        prompts: List[MCPPromptSchema],
        template: Dict[str, Any],
        api_config: Dict[str, Any] = None,
    ):
        """Generate Python MCP Server"""

        # Create src directory
        src_dir = server_dir / "src"
        src_dir.mkdir(exist_ok=True)

        # Generate server.py
        server_code = f'''"""
{display_name} - MCP Server
{description}

This is an MCP Server that exposes tools, resources, and prompts
to MCP Clients (like Teams or Claude) via the Model Context Protocol.
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    Resource,
    Prompt,
    TextContent,
    ImageContent,
    EmbeddedResource,
    PromptMessage,
    PromptArgument,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)
from pydantic import BaseModel, Field, ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='[{name}] %(message)s')
logger = logging.getLogger("{display_name}")

# Tool parameter models for validation
{self._generate_pydantic_models(tools)}

# Tools exposed by this server
TOOLS: List[Tool] = {json.dumps([t.to_dict() for t in tools], indent=4)}

# Resources exposed by this server
RESOURCES: List[Resource] = {json.dumps([r.to_dict() for r in resources], indent=4)}

# Prompts provided by this server
PROMPTS: List[Prompt] = {json.dumps([p.to_dict() for p in prompts], indent=4)}


class {self._to_class_name(name)}Server:
    """
    MCP Server for {display_name}
    This server can be used by any MCP Client through the Model Context Protocol
    """

    def __init__(self):
        logger.info("Initializing MCP Server...")
        self.server = Server("{name}")
        self._setup_handlers()
        logger.info("Server initialized successfully")

    def _setup_handlers(self):
        """Setup all request handlers for the MCP Server"""

        # Tool handlers - expose tools to MCP Clients
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            logger.info("Client requested tool list")
            return TOOLS

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[TextContent]:
            logger.info(f"Client calling tool: {{name}}")

            try:
                if name not in [tool["name"] for tool in TOOLS]:
                    raise ValueError(f"Unknown tool: {{name}}")

                # Validate and call the appropriate tool
                result = await self._call_tool(name, arguments or {{}})

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except ValidationError as e:
                logger.error(f"Validation error: {{e}}")
                raise McpError(INVALID_PARAMS, f"Invalid parameters: {{str(e)}}")
            except Exception as e:
                logger.error(f"Tool error: {{e}}")
                raise McpError(INTERNAL_ERROR, str(e))

        # Resource handlers - expose data to MCP Clients
        if RESOURCES:
            @self.server.list_resources()
            async def handle_list_resources() -> List[Resource]:
                logger.info("Client requested resource list")
                return RESOURCES

            @self.server.read_resource()
            async def handle_read_resource(uri: str) -> str:
                logger.info(f"Client reading resource: {{uri}}")

                resource = next((r for r in RESOURCES if r["uri"] == uri), None)
                if not resource:
                    raise ValueError(f"Unknown resource: {{uri}}")

                return await self._read_resource(uri)

        # Prompt handlers - provide prompts to MCP Clients
        if PROMPTS:
            @self.server.list_prompts()
            async def handle_list_prompts() -> List[Prompt]:
                logger.info("Client requested prompt list")
                return PROMPTS

            @self.server.get_prompt()
            async def handle_get_prompt(
                name: str,
                arguments: Optional[Dict[str, str]]
            ) -> Optional[PromptMessage]:
                logger.info(f"Client getting prompt: {{name}}")

                prompt = next((p for p in PROMPTS if p["name"] == name), None)
                if not prompt:
                    raise ValueError(f"Unknown prompt: {{name}}")

                return await self._get_prompt(name, arguments or {{}})

    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Route tool calls to appropriate handlers"""
        {self._generate_python_tool_handlers(tools)}

        raise ValueError(f"Tool {{name}} not implemented")

{self._generate_python_tool_implementations(tools, server_type)}

    async def _read_resource(self, uri: str) -> str:
        """Read and return resource content"""
        logger.info(f"Reading resource: {{uri}}")
        # TODO: Implement resource reading logic
        return json.dumps({{
            "message": f"Resource content for {{uri}}",
            "timestamp": datetime.now().isoformat()
        }})

    async def _get_prompt(self, name: str, arguments: Dict[str, str]) -> PromptMessage:
        """Generate prompt messages for MCP Clients"""
        logger.info(f"Generating prompt: {{name}}")
        # TODO: Implement prompt generation logic
        return PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"Prompt {{name}} with args: {{json.dumps(arguments)}}"
            )
        )

    async def run(self):
        """Run the MCP Server"""
        logger.info("Starting MCP Server...")

        async with stdio_server() as (read_stream, write_stream):
            init_options = InitializationOptions(
                server_name="{name}",
                server_version="1.0.0",
                capabilities={{
                    "tools": {{"listTools": {{}}, "callTool": {{}}}},
                    "resources": {{"listResources": {{}}, "readResource": {{}}}} if RESOURCES else {{}},
                    "prompts": {{"listPrompts": {{}}, "getPrompt": {{}}}} if PROMPTS else {{}},
                }}
            )

            await self.server.run(
                read_stream,
                write_stream,
                init_options,
                raise_exceptions=True,
            )

            logger.info("MCP Server running - ready for client connections")


async def main():
    """Main entry point for the MCP Server"""
    server = {self._to_class_name(name)}Server()

    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {{e}}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
'''

        with open(src_dir / "server.py", "w") as f:
            f.write(server_code)

        # Generate requirements.txt
        requirements = """mcp>=0.1.0
pydantic>=2.0.0
python-dotenv>=1.0.0
"""

        if server_type == "external":
            requirements += "httpx>=0.25.0\n"

        with open(server_dir / "requirements.txt", "w") as f:
            f.write(requirements)

    def _generate_server_manifest(
        self,
        server_dir: Path,
        name: str,
        display_name: str,
        description: str,
        language: str,
        transport: str,
        tools: List[MCPToolSchema],
        resources: List[MCPResourceSchema],
        prompts: List[MCPPromptSchema],
    ):
        """Generate MCP Server manifest"""
        manifest = {
            "type": "mcp-server",
            "name": name,
            "version": "1.0.0",
            "displayName": display_name,
            "description": description,
            "author": "ELF Automations",
            "license": "MIT",
            "runtime": {"type": language, "transport": transport},
            "provides": {
                "tools": [t.to_dict() for t in tools],
                "resources": [r.to_dict() for r in resources],
                "prompts": [p.to_dict() for p in prompts],
            },
            "configuration": {"environment": [], "required": [], "optional": []},
        }

        with open(server_dir / "mcp-manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

    def _generate_server_readme(
        self,
        server_dir: Path,
        name: str,
        display_name: str,
        description: str,
        server_type: str,
        tools: List[MCPToolSchema],
        resources: List[MCPResourceSchema],
        prompts: List[MCPPromptSchema],
    ):
        """Generate comprehensive README for MCP Server"""
        readme = f"""# {display_name} - MCP Server

{description}

## Overview

This is an MCP Server that implements the Model Context Protocol to expose tools, resources, and prompts to MCP Clients.

**Server Type**: {server_type.replace("-", " ").title()}
**Protocol**: Model Context Protocol (MCP)
**Transport**: stdio (standard input/output)

## What This Server Provides

### Tools ({len(tools)})
Tools are functions that MCP Clients can call to perform actions.
"""

        for tool in tools:
            readme += f"\n#### `{tool.name}`\n{tool.description}\n"
            if tool.inputSchema.get("properties"):
                readme += "\n**Parameters:**\n"
                for prop, schema in tool.inputSchema["properties"].items():
                    required = (
                        "required"
                        if prop in tool.inputSchema.get("required", [])
                        else "optional"
                    )
                    readme += f"- `{prop}` ({schema.get('type', 'any')}, {required}): {schema.get('description', '')}\n"

        if resources:
            readme += f"\n### Resources ({len(resources)})\nResources are data that MCP Clients can read.\n"
            for resource in resources:
                readme += f"\n#### `{resource.uri}`\n{resource.description}\n"
                readme += f"- **Type**: {resource.mimeType}\n"

        if prompts:
            readme += f"\n### Prompts ({len(prompts)})\nPrompts help MCP Clients interact with LLMs.\n"
            for prompt in prompts:
                readme += f"\n#### `{prompt.name}`\n{prompt.description}\n"
                if prompt.arguments:
                    readme += "\n**Arguments:**\n"
                    for arg in prompt.arguments:
                        req = "required" if arg.get("required", True) else "optional"
                        readme += f"- `{arg['name']}` ({req}): {arg['description']}\n"

        readme += (
            """
## How MCP Clients Use This Server

### 1. Through AgentGateway (Recommended)
Teams and other services connect to this server via AgentGateway:

```python
from elf_automations.shared.mcp import MCPClient

# The client handles all connection details
client = MCPClient(team_id="my-team")

# Call a tool on this server
result = await client.call_tool(
    server=\""""
            + name
            + """\",
    tool="example_tool",
    arguments={"param": "value"}
)
```

### 2. Direct Connection (Development)
For testing, MCP Clients can connect directly:

```bash
# Using the MCP CLI
mcp connect stdio ./dist/server.js

# Or with Claude Desktop
# Add to Claude Desktop config
```

## Installation

```bash
npm install  # TypeScript
# or
pip install -r requirements.txt  # Python
```

## Development

```bash
# Run in development mode
npm run dev  # TypeScript
# or
python src/server.py  # Python
```

## Building for Production

```bash
# TypeScript
npm run build
npm start

# Python
python -m pip install -e .
```

## Docker Deployment

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY dist ./dist
CMD ["node", "dist/server.js"]
```

## Integration with ELF Automations

This MCP Server is automatically discovered by AgentGateway through:
1. Kubernetes ConfigMap labels
2. Dynamic registration API
3. GitOps deployment

Once deployed, any Team (MCP Client) can use this server's tools.

## Extending This Server

To add new tools:
1. Define the tool schema in the TOOLS array
2. Implement the tool handler method
3. Add validation using Zod/Pydantic
4. Update documentation

## Troubleshooting

### Server won't start
- Check all dependencies are installed
- Verify Node.js/Python version compatibility
- Check for port conflicts (HTTP transport only)

### Clients can't connect
- Verify server is running
- Check AgentGateway logs
- Ensure proper authentication

### Tools failing
- Check parameter validation
- Review server logs
- Test with MCP inspector

## License

MIT
"""
        )

        with open(server_dir / "README.md", "w") as f:
            f.write(readme)

    def _generate_zod_schemas(self, tools: List[MCPToolSchema]) -> str:
        """Generate Zod schemas for TypeScript"""
        schemas = []

        for tool in tools:
            if not tool.inputSchema.get("properties"):
                continue

            schema_name = f"{self._to_camel_case(tool.name)}Schema"
            schema_lines = [f"const {schema_name} = z.object({{"]

            for prop_name, prop_schema in tool.inputSchema["properties"].items():
                zod_type = self._json_schema_to_zod(prop_schema)
                optional = prop_name not in tool.inputSchema.get("required", [])

                if optional:
                    zod_type += ".optional()"

                schema_lines.append(f"  {prop_name}: {zod_type},")

            schema_lines.append("});")
            schema_lines.append(
                f"type {self._to_class_name(tool.name)}Args = z.infer<typeof {schema_name}>;"
            )
            schemas.append("\n".join(schema_lines))

        return "\n\n".join(schemas)

    def _json_schema_to_zod(self, schema: Dict[str, Any]) -> str:
        """Convert JSON Schema to Zod schema"""
        type_map = {
            "string": "z.string()",
            "number": "z.number()",
            "integer": "z.number().int()",
            "boolean": "z.boolean()",
            "object": "z.object({})",
            "array": "z.array(z.any())",
        }

        zod = type_map.get(schema.get("type", "any"), "z.any()")

        # Add constraints
        if "pattern" in schema:
            zod = zod.replace(")", f".regex(/{schema['pattern']}/)")
        if "enum" in schema:
            values = ", ".join(f'"{v}"' for v in schema["enum"])
            zod = f"z.enum([{values}])"
        if "minimum" in schema:
            zod = zod.replace(")", f".min({schema['minimum']})")
        if "maximum" in schema:
            zod = zod.replace(")", f".max({schema['maximum']})")

        # Add description
        if "description" in schema:
            zod = zod.replace(")", f'.describe("{schema["description"]}")')

        return zod

    def _generate_tool_switch_cases(self, tools: List[MCPToolSchema]) -> str:
        """Generate switch cases for tool handling"""
        cases = []

        for tool in tools:
            schema_name = (
                f"{self._to_camel_case(tool.name)}Schema"
                if tool.inputSchema.get("properties")
                else None
            )

            case = f"""          case "{tool.name}": {{
            {f"const validatedArgs = {schema_name}.parse(args);" if schema_name else ""}
            const result = await this.{self._to_camel_case(tool.name)}({f"validatedArgs" if schema_name else "args"});
            return [{{ type: "text", text: JSON.stringify(result, null, 2) }}];
          }}"""

            cases.append(case)

        return "\n".join(cases)

    def _generate_tool_implementations(
        self, tools: List[MCPToolSchema], server_type: str
    ) -> str:
        """Generate tool implementation methods"""
        implementations = []

        for tool in tools:
            params = (
                "args: any"
                if not tool.inputSchema.get("properties")
                else f"args: {self._to_class_name(tool.name)}Args"
            )

            if server_type == "external":
                # For external wrappers, forward to external server
                impl = f"""  private async {self._to_camel_case(tool.name)}({params}): Promise<any> {{
    console.error("[{tool.name}] Forwarding to external MCP server");

    try {{
      // TODO: Forward this request to the external MCP server
      // Example using axios:
      // const response = await axios.post(`${{this.externalUrl}}/tools/{tool.name}`, args);
      // return response.data;

      return {{
        success: true,
        message: "Forwarded to external server",
        result: {{}}
      }};
    }} catch (error) {{
      console.error("[{tool.name}] External server error:", error);
      throw new McpError(ErrorCode.InternalError, "External server error");
    }}
  }}"""
            else:
                # For internal servers, implement the logic
                if template.get("focus") == "api-facade" and tool.name == "query_api":
                    impl = f"""  private async {self._to_camel_case(tool.name)}({params}): Promise<any> {{
    console.error("[{tool.name}] Processing natural language query");

    try {{
      // Find best matching endpoint for the query
      const endpoint = await this.findBestEndpoint(args.query);
      if (!endpoint) {{
        return {{
          success: false,
          message: "No matching API endpoint found for query",
          query: args.query
        }};
      }}

      // Make the API request
      const result = await this.makeApiRequest(endpoint);

      return {{
        success: true,
        message: `Successfully executed query via ${{endpoint}}`,
        endpoint: endpoint,
        result: result
      }};
    }} catch (error: any) {{
      console.error(`[{tool.name}] Query failed: ${{error.message}}`);
      return {{
        success: false,
        message: error.message,
        query: args.query
      }};
    }}
  }}"""
                elif (
                    template.get("focus") == "api-facade"
                    and tool.name == "search_capabilities"
                ):
                    impl = f"""  private async {self._to_camel_case(tool.name)}({params}): Promise<any> {{
    console.error("[{tool.name}] Searching API capabilities");

    if (!this.apiSchema?.paths) {{
      return {{
        success: false,
        message: "API schema not loaded yet"
      }};
    }}

    const searchTerm = args.search_term.toLowerCase();
    const matches: any[] = [];

    Object.entries(this.apiSchema.paths).forEach(([path, operations]: [string, any]) => {{
      if (path.toLowerCase().includes(searchTerm)) {{
        Object.entries(operations).forEach(([method, operation]: [string, any]) => {{
          matches.push({{
            path: path,
            method: method.toUpperCase(),
            summary: operation.summary || "No summary",
            description: operation.description || "No description",
            tags: operation.tags || []
          }});
        }});
      }}
    }});

    return {{
      success: true,
      message: `Found ${{matches.length}} matching endpoints`,
      search_term: args.search_term,
      matches: matches.slice(0, 20) // Limit results
    }};
  }}"""
                elif (
                    template.get("focus") == "api-facade"
                    and tool.name == "get_api_schema"
                ):
                    impl = f"""  private async {self._to_camel_case(tool.name)}({params}): Promise<any> {{
    console.error("[{tool.name}] Getting API schema for endpoint");

    if (!this.apiSchema?.paths) {{
      return {{
        success: false,
        message: "API schema not loaded yet"
      }};
    }}

    const endpointSchema = this.apiSchema.paths[args.endpoint];
    if (!endpointSchema) {{
      return {{
        success: false,
        message: `Endpoint ${{args.endpoint}} not found in API schema`
      }};
    }}

    return {{
      success: true,
      message: `Schema for endpoint ${{args.endpoint}}`,
      endpoint: args.endpoint,
      schema: endpointSchema
    }};
  }}"""
                else:
                    impl = f"""  private async {self._to_camel_case(tool.name)}({params}): Promise<any> {{
    console.error("[{tool.name}] Processing request");

    // TODO: Implement {tool.name} logic
    // This is where the actual tool functionality goes

    return {{
      success: true,
      message: "Successfully executed {tool.name}",
      result: {{
        // Return actual results here
      }}
    }};
  }}"""

            implementations.append(impl)

        return "\n\n".join(implementations)

    def _generate_pydantic_models(self, tools: List[MCPToolSchema]) -> str:
        """Generate Pydantic models for Python"""
        models = []

        for tool in tools:
            if not tool.inputSchema.get("properties"):
                continue

            model_name = f"{self._to_class_name(tool.name)}Args"
            model_lines = [f"class {model_name}(BaseModel):"]
            model_lines.append(f'    """Arguments for {tool.name} tool"""')

            for prop_name, prop_schema in tool.inputSchema["properties"].items():
                field_type = self._json_schema_to_python_type(prop_schema)
                required = prop_name in tool.inputSchema.get("required", [])

                if required:
                    model_lines.append(
                        f'    {prop_name}: {field_type} = Field(description="{prop_schema.get("description", "")}")'
                    )
                else:
                    model_lines.append(
                        f'    {prop_name}: Optional[{field_type}] = Field(None, description="{prop_schema.get("description", "")}")'
                    )

            models.append("\n".join(model_lines))

        return "\n\n".join(models) if models else "# No parameter models needed"

    def _json_schema_to_python_type(self, schema: Dict[str, Any]) -> str:
        """Convert JSON Schema to Python type"""
        type_map = {
            "string": "str",
            "number": "float",
            "integer": "int",
            "boolean": "bool",
            "object": "Dict[str, Any]",
            "array": "List[Any]",
        }

        if "enum" in schema:
            return f"Literal[{', '.join(repr(v) for v in schema['enum'])}]"

        return type_map.get(schema.get("type", "any"), "Any")

    def _generate_python_tool_handlers(self, tools: List[MCPToolSchema]) -> str:
        """Generate Python tool handler dispatching"""
        handlers = []

        for tool in tools:
            model_name = (
                f"{self._to_class_name(tool.name)}Args"
                if tool.inputSchema.get("properties")
                else None
            )

            handler = f"""if name == "{tool.name}":
            {f"validated_args = {model_name}(**arguments)" if model_name else ""}
            return await self._{tool.name.replace("-", "_")}({f"validated_args" if model_name else "arguments"})"""

            handlers.append(handler)

        return "\n        ".join(handlers)

    def _generate_python_tool_implementations(
        self, tools: List[MCPToolSchema], server_type: str
    ) -> str:
        """Generate Python tool implementations"""
        implementations = []

        for tool in tools:
            model_name = (
                f"{self._to_class_name(tool.name)}Args"
                if tool.inputSchema.get("properties")
                else None
            )
            params = f"args: {model_name}" if model_name else "args: Dict[str, Any]"

            if server_type == "external":
                # For external wrappers
                impl = f'''    async def _{tool.name.replace("-", "_")}(self, {params}) -> Dict[str, Any]:
        """Forward {tool.name} to external MCP server"""
        logger.info(f"Forwarding {{tool.name}} to external server")

        try:
            # TODO: Forward this request to the external MCP server
            # Example using httpx:
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(f"{{self.external_url}}/tools/{tool.name}", json=args)
            #     return response.json()

            return {{
                "success": True,
                "message": "Forwarded to external server",
                "result": {{}}
            }}
        except Exception as e:
            logger.error(f"External server error: {{e}}")
            raise'''
            else:
                # For internal servers
                impl = f'''    async def _{tool.name.replace("-", "_")}(self, {params}) -> Dict[str, Any]:
        """Implement {tool.name} tool"""
        logger.info(f"Processing {{tool.name}}")

        # TODO: Implement {tool.name} logic
        # This is where the actual tool functionality goes

        return {{
            "success": True,
            "message": f"Successfully executed {tool.name}",
            "result": {{
                # Return actual results here
            }}
        }}'''

            implementations.append(impl)

        return "\n\n".join(implementations)

    def _generate_agentgateway_config(
        self,
        server_dir: Path,
        name: str,
        display_name: str,
        description: str,
        transport: str,
        tools: List[MCPToolSchema],
        resources: List[MCPResourceSchema],
    ):
        """Generate AgentGateway configuration for this MCP Server"""
        config = {
            "name": name,
            "displayName": display_name,
            "description": f"{description} (MCP Server)",
            "type": "mcp-server",
            "protocol": transport,
            "tools": [t.to_dict() for t in tools],
            "resources": [r.to_dict() for r in resources],
            "healthCheck": {
                "enabled": True,
                "interval": 30000,
                "timeout": 5000,
                "tool": tools[0].name if tools else None,
            },
        }

        with open(server_dir / "agentgateway-config.json", "w") as f:
            json.dump(config, f, indent=2)

    def _generate_kubernetes_manifests(
        self, server_dir: Path, name: str, display_name: str, language: str
    ):
        """Generate Kubernetes manifests for the MCP Server"""
        k8s_dir = server_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)

        # ConfigMap with registration label
        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{name}-config",
                "namespace": "elf-mcps",
                "labels": {
                    "app": name,
                    "type": "mcp-server",
                    "agentgateway.elfautomations.com/register": "true",
                },
            },
            "data": {
                "agentgateway-config.json": json.dumps(
                    json.loads((server_dir / "agentgateway-config.json").read_text()),
                    indent=2,
                )
            },
        }

        with open(k8s_dir / "configmap.yaml", "w") as f:
            yaml.dump(configmap, f, default_flow_style=False)

        # Deployment
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": name,
                "namespace": "elf-mcps",
                "labels": {"app": name, "type": "mcp-server"},
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": name}},
                "template": {
                    "metadata": {"labels": {"app": name, "type": "mcp-server"}},
                    "spec": {
                        "containers": [
                            {
                                "name": name,
                                "image": f"elf-automations/{name}:latest",
                                "imagePullPolicy": "Never",
                                "resources": {
                                    "requests": {"memory": "256Mi", "cpu": "100m"},
                                    "limits": {"memory": "512Mi", "cpu": "500m"},
                                },
                            }
                        ]
                    },
                },
            },
        }

        with open(k8s_dir / "deployment.yaml", "w") as f:
            yaml.dump(deployment, f, default_flow_style=False)

    def _generate_tsconfig(self, server_dir: Path):
        """Generate tsconfig.json"""
        tsconfig = {
            "compilerOptions": {
                "target": "ES2022",
                "module": "Node16",
                "moduleResolution": "Node16",
                "outDir": "./dist",
                "rootDir": "./src",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True,
                "resolveJsonModule": True,
                "declaration": True,
                "declarationMap": True,
                "sourceMap": True,
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist"],
        }

        with open(server_dir / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)

    def _generate_gitignore(self, server_dir: Path):
        """Generate .gitignore"""
        gitignore = """node_modules/
dist/
*.log
.env
.DS_Store
coverage/
.vscode/
*.js.map
__pycache__/
*.pyc
.pytest_cache/
"""

        with open(server_dir / ".gitignore", "w") as f:
            f.write(gitignore)

    def _generate_api_facade_constants(self, api_config: Dict[str, Any]) -> str:
        """Generate API facade specific constants"""
        if not api_config:
            return ""

        return f"""
// API Configuration
const API_BASE_URL = "{api_config.get('base_url', '')}";
const API_DOCS_URL = "{api_config.get('docs_url', '')}";
const API_KEY_NAME = "{api_config.get('api_key_name', 'X-API-Key')}";
const API_KEY_TYPE = "{api_config.get('api_key_type', 'header')}";

// Cache for API documentation
let apiSchema: any = null;
let endpointCache: Map<string, any> = new Map();
"""

    def _generate_api_facade_properties(self, api_config: Dict[str, Any]) -> str:
        """Generate API facade specific class properties"""
        if not api_config:
            return ""

        return f"""
  private apiClient: AxiosInstance;
  private apiKey: string | null = null;
  private apiSchema: any = null;"""

    def _generate_api_facade_constructor_init(self, api_config: Dict[str, Any]) -> str:
        """Generate API facade specific constructor initialization"""
        if not api_config:
            return ""

        auth_setup = ""
        if api_config.get("requires_api_key"):
            auth_setup = """
    // Get API key from environment
    this.apiKey = process.env.API_KEY || process.env[`${API_KEY_NAME}`];
    if (!this.apiKey) {
      console.warn("[API Facade] No API key found. Some endpoints may fail.");
    }"""

        return f"""
    // Initialize API client
    this.apiClient = axios.create({{
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {{
        "Content-Type": "application/json",
        "User-Agent": "ELF-Automations-MCP-Server/1.0.0"
      }}
    }});{auth_setup}

    // Load API documentation
    this.loadApiDocumentation();"""

    def _generate_api_facade_methods(self, api_config: Dict[str, Any]) -> str:
        """Generate API facade specific methods"""
        if not api_config:
            return ""

        return f"""
  private async loadApiDocumentation(): Promise<void> {{
    try {{
      console.error("[API Facade] Loading API documentation...");
      const response = await axios.get(API_DOCS_URL);

      if (API_DOCS_URL.endsWith('.json')) {{
        this.apiSchema = response.data;
      }} else if (API_DOCS_URL.endsWith('.yaml') || API_DOCS_URL.endsWith('.yml')) {{
        this.apiSchema = load(response.data);
      }} else {{
        console.error("[API Facade] Unsupported documentation format");
        return;
      }}

      console.error(`[API Facade] Loaded API schema with ${{Object.keys(this.apiSchema.paths || {{}}).length}} endpoints`);
    }} catch (error) {{
      console.error(`[API Facade] Failed to load API documentation: ${{error}}`);
    }}
  }}

  private async makeApiRequest(endpoint: string, method: string = 'GET', data?: any): Promise<any> {{
    try {{
      const config: any = {{
        method,
        url: endpoint,
        data
      }};

      // Add API key if required
      if (this.apiKey) {{
        if (API_KEY_TYPE === 'header') {{
          config.headers = {{ [API_KEY_NAME]: this.apiKey }};
        }} else if (API_KEY_TYPE === 'query') {{
          config.params = {{ [API_KEY_NAME]: this.apiKey }};
        }} else if (API_KEY_TYPE === 'bearer') {{
          config.headers = {{ Authorization: `Bearer ${{this.apiKey}}` }};
        }}
      }}

      const response = await this.apiClient.request(config);
      return response.data;
    }} catch (error: any) {{
      console.error(`[API Facade] API request failed: ${{error.message}}`);
      throw new McpError(
        ErrorCode.InternalError,
        `API request failed: ${{error.message}}`
      );
    }}
  }}

  private async findBestEndpoint(query: string): Promise<string | null> {{
    if (!this.apiSchema?.paths) {{
      return null;
    }}

    // Simple matching - find endpoints that match query terms
    const queryLower = query.toLowerCase();
    const endpoints = Object.keys(this.apiSchema.paths);

    // Score endpoints based on path and description matches
    const scored = endpoints.map(endpoint => {{
      let score = 0;
      const endpointLower = endpoint.toLowerCase();

      // Direct path matches
      if (endpointLower.includes(queryLower)) score += 10;

      // Check operation descriptions
      const operations = this.apiSchema.paths[endpoint];
      Object.values(operations || {{}}).forEach((op: any) => {{
        if (op.summary?.toLowerCase().includes(queryLower)) score += 5;
        if (op.description?.toLowerCase().includes(queryLower)) score += 3;
        op.tags?.forEach((tag: string) => {{
          if (tag.toLowerCase().includes(queryLower)) score += 2;
        }});
      }});

      return {{ endpoint, score }};
    }})
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score);

    return scored.length > 0 ? scored[0].endpoint : null;
  }}"""

    def _to_class_name(self, name: str) -> str:
        """Convert kebab-case to PascalCase"""
        return "".join(word.capitalize() for word in name.split("-"))

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case to camelCase"""
        parts = name.split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])

    def _print_next_steps(self, name: str, language: str, server_type: str):
        """Print next steps after generation"""
        console.print("\n[bold cyan]Next Steps:[/bold cyan]")

        console.print(f"\n1. [yellow]Review and implement tool logic:[/yellow]")
        console.print(f"   cd mcp-servers/{name}/src")
        console.print(f"   # Edit server.{'ts' if language == 'typescript' else 'py'}")

        console.print(f"\n2. [yellow]Install dependencies:[/yellow]")
        if language == "typescript":
            console.print("   npm install")
        else:
            console.print("   pip install -r requirements.txt")

        console.print(f"\n3. [yellow]Test your MCP Server locally:[/yellow]")
        if language == "typescript":
            console.print("   npm run dev")
        else:
            console.print("   python src/server.py")

        console.print(f"\n4. [yellow]Test with an MCP Client:[/yellow]")
        console.print("   # In another terminal:")
        console.print("   mcp-cli connect stdio 'node dist/server.js'")
        console.print("   # Or configure in Claude Desktop")

        console.print(f"\n5. [yellow]Deploy to ELF Automations:[/yellow]")
        console.print(f"   docker build -t elf-automations/{name}:latest .")
        console.print(f"   # Then deploy via GitOps")

        console.print(f"\n[green]Your MCP Server is ready![/green]")
        console.print(
            f"[dim]MCP Clients (Teams, Claude) can connect to this server[/dim]"
        )

        if server_type == "external":
            console.print(
                f"\n[yellow]Note: This is a wrapper for an external MCP Server[/yellow]"
            )
            console.print(
                f"[dim]You'll need to implement the forwarding logic to the external server[/dim]"
            )


def list_mcp_servers():
    """List existing MCP Servers"""
    servers_dir = Path(__file__).parent.parent / "mcp-servers"

    if not servers_dir.exists():
        console.print("[yellow]No MCP Servers found[/yellow]")
        return

    table = Table(title="MCP Servers in Project")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Language", style="yellow")
    table.add_column("Tools", style="blue")
    table.add_column("Resources", style="magenta")

    for server_path in servers_dir.iterdir():
        if server_path.is_dir():
            manifest_path = server_path / "mcp-manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)

                table.add_row(
                    manifest.get("name", server_path.name),
                    manifest.get("type", "internal"),
                    manifest.get("runtime", {}).get("type", "unknown"),
                    str(len(manifest.get("provides", {}).get("tools", []))),
                    str(len(manifest.get("provides", {}).get("resources", []))),
                )

    console.print(table)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MCP Server Factory - Create servers that expose tools via Model Context Protocol"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new MCP Server")

    # List command
    list_parser = subparsers.add_parser("list", help="List existing MCP Servers")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate an MCP Server")
    validate_parser.add_argument("path", help="Path to MCP Server directory")

    args = parser.parse_args()

    if args.command == "create" or args.command is None:
        factory = MCPServerFactory()
        factory.create_mcp_server()
    elif args.command == "list":
        list_mcp_servers()
    elif args.command == "validate":
        console.print("[yellow]Validation feature coming soon![/yellow]")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
