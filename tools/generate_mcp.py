#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Generator for Internal Tools
Automatically creates MCP servers and registers them with AgentGateway

This script:
1. Generates MCP server code based on tool specifications
2. Creates proper TypeScript/Python implementations
3. Registers the MCP with AgentGateway for discovery
4. Makes tools available to all agents in the ElfAutomations ecosystem
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


@dataclass
class ToolSpec:
    """Specification for a tool to be exposed via MCP"""

    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    implementation: str  # Python code or API endpoint


@dataclass
class MCPSpec:
    """Complete MCP server specification"""

    name: str
    version: str
    description: str
    tools: List[ToolSpec]
    resources: List[Dict[str, Any]] = None
    language: str = "python"  # or "typescript"


class MCPGenerator:
    """Generates MCP servers and registers them with AgentGateway"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.mcp_internal_dir = self.project_root / "mcp" / "internal"
        self.agentgateway_config = (
            self.project_root / "config" / "agentgateway" / "config.json"
        )

    def generate_mcp(self, spec: MCPSpec):
        """Generate a complete MCP server from specification"""
        print(f"🔧 Generating MCP server: {spec.name}")

        if spec.language == "python":
            self._generate_python_mcp(spec)
        else:
            self._generate_typescript_mcp(spec)

        # Register with AgentGateway
        self._register_with_agentgateway(spec)

        print(f"✅ MCP server '{spec.name}' generated and registered!")

    def _generate_python_mcp(self, spec: MCPSpec):
        """Generate Python-based MCP server"""
        # Create directory
        mcp_dir = self.mcp_internal_dir / "python" / spec.name.replace("-", "_")
        mcp_dir.mkdir(parents=True, exist_ok=True)

        # Generate server.py
        server_content = f'''#!/usr/bin/env python3
"""
{spec.name} MCP Server
{spec.description}

Auto-generated by MCP Generator
"""

import sys
import json
from typing import Any, Dict
from mcp_servers.base import BaseMCPServer, MCPTool

class {self._to_class_name(spec.name)}MCPServer(BaseMCPServer):
    """MCP Server for {spec.name}"""

    def __init__(self):
        super().__init__("{spec.name}", "{spec.version}")
        self._register_tools()

    def _register_tools(self):
        """Register all tools provided by this server"""
'''

        # Add tool registrations
        for tool in spec.tools:
            server_content += f"""
        self.register_tool(
            name="{tool.name}",
            description="{tool.description}",
            parameters={json.dumps(tool.parameters, indent=16).replace('"', "'")},
            handler=self._{tool.name.replace("-", "_")}
        )
"""

        # Add tool implementations
        server_content += "\n    # Tool implementations\n"
        for tool in spec.tools:
            server_content += f'''
    async def _{tool.name.replace("-", "_")}(self, **kwargs) -> Dict[str, Any]:
        """{tool.description}"""
        try:
{self._indent_code(tool.implementation, 12)}
        except Exception as e:
            return {{"error": str(e)}}
'''

        # Add main runner
        server_content += (
            '''

async def main():
    """Run the MCP server"""
    server = '''
            + self._to_class_name(spec.name)
            + """MCPServer()

    # Read from stdin and write to stdout (MCP protocol)
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            response = await server.handle_request(request)

            print(json.dumps(response))
            sys.stdout.flush()

        except Exception as e:
            error_response = {
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
"""
        )

        # Write server file
        server_file = mcp_dir / "server.py"
        with open(server_file, "w") as f:
            f.write(server_content)
        os.chmod(server_file, 0o755)

        # Create __init__.py
        init_file = mcp_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write(f'"""MCP Server for {spec.name}"""')

        # Create requirements.txt
        requirements = ["structlog", "pydantic", "aiofiles", "asyncio"]
        req_file = mcp_dir / "requirements.txt"
        with open(req_file, "w") as f:
            f.write("\n".join(requirements))

    def _generate_typescript_mcp(self, spec: MCPSpec):
        """Generate TypeScript-based MCP server"""
        # Create directory
        mcp_dir = self.mcp_internal_dir / "typescript" / spec.name
        mcp_dir.mkdir(parents=True, exist_ok=True)

        # Generate server.ts
        server_content = f"""/**
 * {spec.name} MCP Server
 * {spec.description}
 *
 * Auto-generated by MCP Generator
 */

import {{ Server, Tool }} from '@modelcontextprotocol/sdk';

const server = new Server({{
  name: '{spec.name}',
  version: '{spec.version}'
}});

// Register tools
"""

        # Add tools
        for tool in spec.tools:
            params_schema = json.dumps(tool.parameters, indent=2)
            server_content += f"""
server.tool({{
  name: '{tool.name}',
  description: '{tool.description}',
  parameters: {params_schema},
  handler: async (params) => {{
    // Implementation
    {self._convert_to_typescript(tool.implementation)}
  }}
}});
"""

        server_content += """
// Start server
server.start();
"""

        # Write server file
        server_file = mcp_dir / "server.ts"
        with open(server_file, "w") as f:
            f.write(server_content)

        # Create package.json
        package_json = {
            "name": f"@elf-automations/{spec.name}",
            "version": spec.version,
            "description": spec.description,
            "main": "dist/server.js",
            "scripts": {"build": "tsc", "start": "node dist/server.js"},
            "dependencies": {"@modelcontextprotocol/sdk": "latest"},
            "devDependencies": {"typescript": "^5.0.0", "@types/node": "^20.0.0"},
        }

        package_file = mcp_dir / "package.json"
        with open(package_file, "w") as f:
            json.dump(package_json, f, indent=2)

        # Create tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "outDir": "./dist",
                "strict": True,
                "esModuleInterop": True,
            },
            "include": ["*.ts"],
            "exclude": ["node_modules"],
        }

        tsconfig_file = mcp_dir / "tsconfig.json"
        with open(tsconfig_file, "w") as f:
            json.dump(tsconfig, f, indent=2)

    def _register_with_agentgateway(self, spec: MCPSpec):
        """Register the MCP server with AgentGateway"""
        print(f"📡 Registering {spec.name} with AgentGateway...")

        # Load current AgentGateway config
        with open(self.agentgateway_config, "r") as f:
            config = json.load(f)

        # Add new MCP target
        if "targets" not in config:
            config["targets"] = {}
        if "mcp" not in config["targets"]:
            config["targets"]["mcp"] = []

        # Create MCP entry based on language
        if spec.language == "python":
            mcp_entry = {
                "name": spec.name,
                "stdio": {
                    "cmd": "python",
                    "args": [
                        f"{self.mcp_internal_dir}/python/{spec.name.replace('-', '_')}/server.py"
                    ],
                },
            }
        else:  # typescript
            mcp_entry = {
                "name": spec.name,
                "stdio": {
                    "cmd": "node",
                    "args": [
                        f"{self.mcp_internal_dir}/typescript/{spec.name}/dist/server.js"
                    ],
                },
            }

        # Check if already registered
        existing = [t for t in config["targets"]["mcp"] if t["name"] == spec.name]
        if existing:
            # Update existing entry
            idx = config["targets"]["mcp"].index(existing[0])
            config["targets"]["mcp"][idx] = mcp_entry
        else:
            # Add new entry
            config["targets"]["mcp"].append(mcp_entry)

        # Write updated config
        with open(self.agentgateway_config, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✅ Registered {spec.name} in AgentGateway config")

        # Restart AgentGateway if running in k8s
        try:
            subprocess.run(
                [
                    "kubectl",
                    "rollout",
                    "restart",
                    "deployment/agentgateway",
                    "-n",
                    "elf-automations",
                ],
                capture_output=True,
            )
            print("🔄 AgentGateway restarted to load new MCP")
        except:
            print("⚠️  Please restart AgentGateway manually to load the new MCP")

    def _to_class_name(self, name: str) -> str:
        """Convert kebab-case to PascalCase"""
        return "".join(word.capitalize() for word in name.split("-"))

    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code block"""
        indent = " " * spaces
        return "\n".join(indent + line for line in code.strip().split("\n"))

    def _convert_to_typescript(self, python_code: str) -> str:
        """Basic Python to TypeScript conversion (simplified)"""
        # This is a very basic conversion - in production you'd want something more sophisticated
        ts_code = python_code
        ts_code = ts_code.replace("Dict[", "Record<")
        ts_code = ts_code.replace("List[", "Array<")
        ts_code = ts_code.replace("return ", "return ")
        return ts_code


def create_example_mcp():
    """Create an example MCP for demonstration"""
    spec = MCPSpec(
        name="team-metrics",
        version="1.0.0",
        description="Provides team performance metrics and analytics",
        tools=[
            ToolSpec(
                name="get-team-metrics",
                description="Get performance metrics for a team",
                parameters={
                    "type": "object",
                    "properties": {
                        "team_name": {
                            "type": "string",
                            "description": "Name of the team",
                        },
                        "period": {"type": "string", "enum": ["day", "week", "month"]},
                    },
                    "required": ["team_name"],
                },
                returns={"type": "object"},
                implementation="""
# Fetch metrics from Supabase
import aiohttp
import os

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

async with aiohttp.ClientSession() as session:
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}"
    }

    async with session.get(
        f"{supabase_url}/rest/v1/team_metrics?team_name=eq.{kwargs['team_name']}",
        headers=headers
    ) as response:
        data = await response.json()

return {
    "team": kwargs['team_name'],
    "metrics": data[0] if data else {},
    "period": kwargs.get('period', 'week')
}
""",
            ),
            ToolSpec(
                name="log-team-event",
                description="Log an event for a team",
                parameters={
                    "type": "object",
                    "properties": {
                        "team_name": {"type": "string"},
                        "event_type": {"type": "string"},
                        "details": {"type": "object"},
                    },
                    "required": ["team_name", "event_type"],
                },
                returns={"type": "object"},
                implementation="""
# Log event to Supabase
import aiohttp
import os
from datetime import datetime

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

event_data = {
    "team_name": kwargs['team_name'],
    "event_type": kwargs['event_type'],
    "details": kwargs.get('details', {}),
    "timestamp": datetime.utcnow().isoformat()
}

async with aiohttp.ClientSession() as session:
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }

    async with session.post(
        f"{supabase_url}/rest/v1/team_events",
        headers=headers,
        json=event_data
    ) as response:
        result = await response.json()

return {"success": True, "event_id": result.get('id')}
""",
            ),
        ],
    )

    return spec


def main():
    parser = argparse.ArgumentParser(description="Generate and register MCP servers")
    parser.add_argument("--name", required=True, help="Name of the MCP server")
    parser.add_argument("--description", required=True, help="Description of the MCP")
    parser.add_argument(
        "--language", choices=["python", "typescript"], default="python"
    )
    parser.add_argument("--example", action="store_true", help="Generate example MCP")

    args = parser.parse_args()

    generator = MCPGenerator()

    if args.example:
        # Generate example
        spec = create_example_mcp()
        generator.generate_mcp(spec)
    else:
        # Interactive mode for creating custom MCP
        print("🎯 Creating custom MCP server...")
        print("This feature is not yet fully implemented.")
        print("Use --example flag to generate an example MCP")


if __name__ == "__main__":
    main()
