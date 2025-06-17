#!/usr/bin/env python3
"""
Enhanced MCP Factory - Intelligent MCP creation for simple and complex scenarios

This enhanced version:
1. Automatically detects complexity level
2. Provides advanced features for complex MCPs
3. Maintains backward compatibility for simple MCPs
4. Includes template system and schema builders
"""

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.tree import Tree

console = Console()


class ComplexityLevel(Enum):
    """MCP complexity levels"""

    SIMPLE = "simple"  # 1-5 tools, basic types
    MODERATE = "moderate"  # 6-10 tools, some complex types
    COMPLEX = "complex"  # 10+ tools, complex schemas, integrations


class ParameterType(Enum):
    """Parameter types for tool definitions"""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    ENUM = "enum"
    ANY = "any"


@dataclass
class ToolParameter:
    """Tool parameter definition"""

    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: Any = None
    enum_values: List[str] = field(default_factory=list)
    properties: Dict[str, "ToolParameter"] = field(
        default_factory=dict
    )  # For object types
    items: Optional["ToolParameter"] = None  # For array types
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None


@dataclass
class ToolDefinition:
    """Complete tool definition"""

    name: str
    description: str
    parameters: Dict[str, ToolParameter]
    returns: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ResourceDefinition:
    """Resource definition for MCPs"""

    name: str
    description: str
    schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPConfig:
    """Enhanced MCP configuration"""

    name: str
    display_name: str
    description: str
    type: str  # 'internal' or 'external'
    language: str  # 'python' or 'typescript'
    source: str  # package name, repo URL, or 'generated'
    tools: List[ToolDefinition]
    resources: List[ResourceDefinition] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    complexity: ComplexityLevel = ComplexityLevel.SIMPLE
    use_mock: bool = False
    templates: List[str] = field(default_factory=list)


class SchemaBuilder:
    """Interactive schema builder for complex types"""

    def __init__(self, console: Console):
        self.console = console

    def build_parameter(
        self, name: str = None, depth: int = 0
    ) -> Optional[ToolParameter]:
        """Build a parameter definition interactively"""
        indent = "  " * depth

        if name is None:
            name = Prompt.ask(f"{indent}Parameter name (or Enter to finish)")
            if not name:
                return None

        # Choose type
        type_choices = [t.value for t in ParameterType]
        param_type = Prompt.ask(
            f"{indent}Type for '{name}'",
            choices=type_choices,
            default=ParameterType.STRING.value,
        )
        param_type = ParameterType(param_type)

        # Description
        description = Prompt.ask(f"{indent}Description for '{name}'")

        # Required?
        required = Confirm.ask(f"{indent}Is '{name}' required?", default=True)

        # Create parameter
        param = ToolParameter(
            name=name, type=param_type, description=description, required=required
        )

        # Type-specific configuration
        if param_type == ParameterType.ENUM:
            values = Prompt.ask(f"{indent}Enum values (comma-separated)")
            param.enum_values = [v.strip() for v in values.split(",")]

        elif param_type == ParameterType.OBJECT:
            self.console.print(
                f"{indent}[yellow]Define properties for object '{name}':[/yellow]"
            )
            while True:
                prop = self.build_parameter(depth=depth + 1)
                if prop is None:
                    break
                param.properties[prop.name] = prop

        elif param_type == ParameterType.ARRAY:
            self.console.print(f"{indent}[yellow]Define array item type:[/yellow]")
            param.items = self.build_parameter(name="item", depth=depth + 1)

        elif param_type == ParameterType.STRING:
            if Confirm.ask(f"{indent}Add pattern validation?", default=False):
                param.pattern = Prompt.ask(f"{indent}Regex pattern")

        elif param_type == ParameterType.NUMBER:
            if Confirm.ask(f"{indent}Add min/max constraints?", default=False):
                param.min_value = float(Prompt.ask(f"{indent}Minimum value"))
                param.max_value = float(Prompt.ask(f"{indent}Maximum value"))

        # Default value
        if not required and param_type in [
            ParameterType.STRING,
            ParameterType.NUMBER,
            ParameterType.BOOLEAN,
        ]:
            if Confirm.ask(f"{indent}Provide default value?", default=False):
                if param_type == ParameterType.BOOLEAN:
                    param.default = Confirm.ask(f"{indent}Default value")
                else:
                    param.default = Prompt.ask(f"{indent}Default value")

        return param


class TemplateLibrary:
    """Library of MCP templates"""

    TEMPLATES = {
        "database": {
            "name": "Database Integration",
            "description": "Connect to databases with CRUD operations",
            "tools": ["query", "insert", "update", "delete", "schema"],
            "dependencies": {
                "python": ["asyncpg", "sqlalchemy"],
                "typescript": ["pg", "typeorm"],
            },
        },
        "vector_search": {
            "name": "Vector Search",
            "description": "Semantic search with embeddings",
            "tools": ["embed", "search", "upsert", "delete"],
            "dependencies": {
                "python": ["qdrant-client", "sentence-transformers"],
                "typescript": ["@qdrant/js-client", "openai"],
            },
        },
        "api_wrapper": {
            "name": "API Wrapper",
            "description": "Wrap external REST APIs",
            "tools": ["get", "post", "put", "delete", "patch"],
            "dependencies": {
                "python": ["httpx", "pydantic"],
                "typescript": ["axios", "zod"],
            },
        },
        "file_operations": {
            "name": "File Operations",
            "description": "File system operations",
            "tools": ["read", "write", "list", "delete", "move"],
            "dependencies": {"python": ["aiofiles"], "typescript": ["fs-extra"]},
        },
        "monitoring": {
            "name": "Monitoring & Analytics",
            "description": "System monitoring and analytics",
            "tools": ["metrics", "logs", "alerts", "dashboard"],
            "dependencies": {
                "python": ["prometheus-client", "structlog"],
                "typescript": ["prom-client", "winston"],
            },
        },
    }

    @classmethod
    def get_template(cls, template_name: str) -> Dict[str, Any]:
        """Get a template by name"""
        return cls.TEMPLATES.get(template_name, {})

    @classmethod
    def list_templates(cls) -> List[str]:
        """List available templates"""
        return list(cls.TEMPLATES.keys())


class MCPFactory:
    """Enhanced MCP Factory with complexity detection"""

    def __init__(self):
        self.console = console
        self.project_root = Path(__file__).parent.parent
        self.mcp_dir = self.project_root / "mcp"
        self.schema_builder = SchemaBuilder(console)

    def create_mcp(self):
        """Main entry point for MCP creation"""
        self.console.print(
            "\n[bold cyan]🔧 Enhanced MCP Factory - Intelligent MCP Creation[/bold cyan]\n"
        )

        # Step 1: Basic information
        name = Prompt.ask("MCP name (e.g., 'analytics-tools')")
        display_name = Prompt.ask(
            "Display name", default=name.replace("-", " ").title()
        )
        description = Prompt.ask("Description")

        # Step 2: Choose implementation language
        language = Prompt.ask(
            "Implementation language",
            choices=["typescript", "python"],
            default="typescript",
        )

        # Step 3: Check if user wants to use templates
        use_templates = Confirm.ask(
            "\nWould you like to use a template as a starting point?", default=False
        )

        templates = []
        if use_templates:
            templates = self._select_templates()

        # Step 4: Define tools
        self.console.print("\n[bold]Define tools for this MCP:[/bold]")
        tools = self._define_tools(templates)

        # Step 5: Define resources (optional)
        resources = []
        if Confirm.ask("\nDoes this MCP expose resources?", default=False):
            resources = self._define_resources()

        # Step 6: Determine complexity
        complexity = self._determine_complexity(tools, resources)
        self.console.print(
            f"\n[yellow]Detected complexity level: {complexity.value}[/yellow]"
        )

        # Step 7: Additional configuration for complex MCPs
        dependencies = []
        dev_dependencies = []
        use_mock = False
        environment = {}

        if complexity != ComplexityLevel.SIMPLE:
            # Dependencies
            if Confirm.ask("\nAdd additional dependencies?", default=True):
                dependencies = self._collect_dependencies(language, templates)

            # Mock support
            use_mock = Confirm.ask(
                "\nInclude mock implementations for development?", default=True
            )

            # Environment variables
            environment = self._collect_environment_vars()

        # Create MCP configuration
        config = MCPConfig(
            name=name,
            display_name=display_name,
            description=description,
            type="internal",
            language=language,
            source="generated",
            tools=tools,
            resources=resources,
            environment=environment,
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            complexity=complexity,
            use_mock=use_mock,
            templates=templates,
        )

        # Generate MCP
        self._generate_mcp(config)

    def _select_templates(self) -> List[str]:
        """Select templates to use"""
        templates = []

        self.console.print("\n[bold]Available Templates:[/bold]")
        for name, info in TemplateLibrary.TEMPLATES.items():
            self.console.print(f"  • [cyan]{name}[/cyan]: {info['description']}")

        while True:
            template = Prompt.ask(
                "\nSelect template (or Enter to continue)",
                choices=TemplateLibrary.list_templates() + [""],
                default="",
            )
            if not template:
                break
            templates.append(template)
            self.console.print(f"[green]Added template: {template}[/green]")

        return templates

    def _define_tools(self, templates: List[str]) -> List[ToolDefinition]:
        """Define tools for the MCP"""
        tools = []

        # Add tools from templates
        for template_name in templates:
            template = TemplateLibrary.get_template(template_name)
            if template:
                self.console.print(
                    f"\n[yellow]Adding tools from template '{template_name}':[/yellow]"
                )
                for tool_name in template.get("tools", []):
                    self.console.print(f"  • {tool_name}")
                    # Create basic tool definition from template
                    tools.append(
                        ToolDefinition(
                            name=tool_name,
                            description=f"{tool_name.title()} operation",
                            parameters={},
                        )
                    )

        # Add custom tools
        self.console.print("\n[bold]Define additional tools:[/bold]")
        self.console.print("[dim]Press Enter with empty name to finish[/dim]")

        while True:
            tool_name = Prompt.ask("\nTool name (or Enter to finish)")
            if not tool_name:
                break

            tool_description = Prompt.ask("Tool description")

            # Complexity check
            define_params = Confirm.ask(
                "Define parameters for this tool?", default=True
            )

            parameters = {}
            if define_params:
                self.console.print(
                    f"\n[yellow]Define parameters for '{tool_name}':[/yellow]"
                )
                while True:
                    param = self.schema_builder.build_parameter()
                    if param is None:
                        break
                    parameters[param.name] = param

            tools.append(
                ToolDefinition(
                    name=tool_name, description=tool_description, parameters=parameters
                )
            )

        return tools

    def _define_resources(self) -> List[ResourceDefinition]:
        """Define resources for the MCP"""
        resources = []

        self.console.print("\n[bold]Define resources:[/bold]")
        self.console.print("[dim]Press Enter with empty name to finish[/dim]")

        while True:
            name = Prompt.ask("\nResource name (or Enter to finish)")
            if not name:
                break

            description = Prompt.ask("Resource description")
            resources.append(ResourceDefinition(name=name, description=description))

        return resources

    def _determine_complexity(
        self, tools: List[ToolDefinition], resources: List[ResourceDefinition]
    ) -> ComplexityLevel:
        """Determine MCP complexity level"""
        tool_count = len(tools)

        # Check for complex parameters
        has_complex_params = any(
            any(
                p.type in [ParameterType.OBJECT, ParameterType.ARRAY]
                for p in tool.parameters.values()
            )
            for tool in tools
        )

        # Determine level
        if tool_count <= 5 and not has_complex_params and len(resources) == 0:
            return ComplexityLevel.SIMPLE
        elif tool_count <= 10 or has_complex_params:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.COMPLEX

    def _collect_dependencies(self, language: str, templates: List[str]) -> List[str]:
        """Collect additional dependencies"""
        deps = []

        # Add template dependencies
        for template_name in templates:
            template = TemplateLibrary.get_template(template_name)
            if template and language in template.get("dependencies", {}):
                deps.extend(template["dependencies"][language])

        # Remove duplicates
        deps = list(set(deps))

        self.console.print("\n[bold]Current dependencies:[/bold]")
        for dep in deps:
            self.console.print(f"  • {dep}")

        # Add more
        while True:
            dep = Prompt.ask("\nAdd dependency (or Enter to continue)", default="")
            if not dep:
                break
            deps.append(dep)

        return deps

    def _collect_environment_vars(self) -> Dict[str, str]:
        """Collect environment variables"""
        env_vars = {}

        self.console.print("\n[bold]Define environment variables:[/bold]")
        self.console.print("[dim]Press Enter with empty name to finish[/dim]")

        while True:
            name = Prompt.ask("\nVariable name (or Enter to finish)")
            if not name:
                break

            description = Prompt.ask(f"Description for {name}")
            required = Confirm.ask(f"Is {name} required?", default=True)

            default = "${" + name + "}"
            if not required:
                default_value = Prompt.ask(f"Default value for {name}", default="")
                if default_value:
                    default = default_value

            env_vars[name] = default

        return env_vars

    def _generate_mcp(self, config: MCPConfig):
        """Generate MCP based on configuration"""
        self.console.print(
            f"\n[bold yellow]📝 Generating {config.complexity.value} MCP: {config.name}[/bold yellow]"
        )

        if config.language == "typescript":
            self._generate_typescript_mcp(config)
        else:
            self._generate_python_mcp(config)

        self.console.print(
            f"[green]✅ MCP '{config.name}' created successfully![/green]"
        )

    def _generate_typescript_mcp(self, config: MCPConfig):
        """Generate TypeScript MCP with full implementation"""
        server_dir = self.mcp_dir / "typescript" / "servers" / config.name
        server_dir.mkdir(parents=True, exist_ok=True)

        # Generate server.ts
        self._generate_typescript_server(config, server_dir)

        # Generate package.json
        self._generate_typescript_package(config, server_dir)

        # Generate tsconfig.json
        self._generate_typescript_config(config, server_dir)

        # Generate README
        self._generate_readme(config, server_dir)

        # Generate mock implementations if needed
        if config.use_mock:
            self._generate_typescript_mocks(config, server_dir)

        # Generate config.json
        self._generate_config_json(config, server_dir)

    def _generate_typescript_server(self, config: MCPConfig, server_dir: Path):
        """Generate TypeScript server implementation"""
        # Convert parameters to Zod schemas
        schemas = self._generate_zod_schemas(config.tools)

        # Generate server code
        server_code = f"""import {{ Tool }} from '@modelcontextprotocol/sdk/types.js';
import {{ z }} from 'zod';
import {{ BaseMCPServer }} from '../../shared/base-server.js';
"""

        # Add dependencies
        if config.use_mock:
            server_code += "\n// Mock implementations\n"
            for dep in config.dependencies:
                if "qdrant" in dep:
                    server_code += (
                        "import { MockQdrantClient } from './mocks/qdrant.js';\n"
                    )
                elif "supabase" in dep:
                    server_code += (
                        "import { createClient } from '@supabase/supabase-js';\n"
                    )

        # Add schemas
        server_code += f"\n// Schema definitions\n{schemas}\n"

        # Add server class
        server_code += f"""
export class {config.display_name.replace(" ", "")}MCPServer extends BaseMCPServer {{
    constructor() {{
        super('{config.name}-mcp-server', '{config.version}');

        // Initialize services
        {self._generate_service_initialization(config)}
    }}

    getTools(): Tool[] {{
        return [
{self._generate_tool_definitions(config.tools)}
        ];
    }}

    async handleToolCall(name: string, args: any): Promise<any> {{
        switch (name) {{
{self._generate_tool_handlers(config.tools)}
            default:
                throw new Error(`Unknown tool: ${{name}}`);
        }}
    }}

{self._generate_tool_implementations(config.tools)}
}}

// Create and start the server
const server = new {config.display_name.replace(" ", "")}MCPServer();
server.start();
"""

        # Write server file
        with open(server_dir / "server.ts", "w") as f:
            f.write(server_code)

    def _generate_zod_schemas(self, tools: List[ToolDefinition]) -> str:
        """Generate Zod schemas from tool definitions"""
        schemas = []

        for tool in tools:
            if not tool.parameters:
                continue

            schema_name = self._to_pascal_case(tool.name) + "Schema"
            schema = f"const {schema_name} = z.object({{\n"

            for param_name, param in tool.parameters.items():
                schema += f"    {param_name}: {self._param_to_zod(param)},\n"

            schema += "});\n"
            schemas.append(schema)

        return "\n".join(schemas)

    def _param_to_zod(self, param: ToolParameter) -> str:
        """Convert parameter to Zod schema"""
        zod_type = ""

        if param.type == ParameterType.STRING:
            zod_type = "z.string()"
            if param.pattern:
                zod_type += f".regex(/{param.pattern}/)"
        elif param.type == ParameterType.NUMBER:
            zod_type = "z.number()"
            if param.min_value is not None:
                zod_type += f".min({param.min_value})"
            if param.max_value is not None:
                zod_type += f".max({param.max_value})"
        elif param.type == ParameterType.BOOLEAN:
            zod_type = "z.boolean()"
        elif param.type == ParameterType.ENUM:
            values = ", ".join(f'"{v}"' for v in param.enum_values)
            zod_type = f"z.enum([{values}])"
        elif param.type == ParameterType.OBJECT:
            # Recursive object definition
            props = []
            for prop_name, prop in param.properties.items():
                props.append(f"{prop_name}: {self._param_to_zod(prop)}")
            zod_type = f"z.object({{ {', '.join(props)} }})"
        elif param.type == ParameterType.ARRAY:
            if param.items:
                zod_type = f"z.array({self._param_to_zod(param.items)})"
            else:
                zod_type = "z.array(z.any())"
        else:
            zod_type = "z.any()"

        # Add description
        if param.description:
            zod_type += f'.describe("{param.description}")'

        # Handle optional
        if not param.required:
            zod_type += ".optional()"

        # Handle default
        if param.default is not None:
            zod_type += f".default({json.dumps(param.default)})"

        return zod_type

    def _generate_tool_definitions(self, tools: List[ToolDefinition]) -> str:
        """Generate tool definitions for getTools()"""
        tool_defs = []

        for tool in tools:
            schema_name = (
                self._to_pascal_case(tool.name) + "Schema" if tool.parameters else None
            )

            tool_def = f"""            {{
                name: '{tool.name}',
                description: '{tool.description}',
                inputSchema: {{
                    type: 'object',
                    properties: {schema_name + '.shape' if schema_name else '{}'},
                    required: [{', '.join(f'"{p}"' for p, param in tool.parameters.items() if param.required)}],
                }},
            }}"""
            tool_defs.append(tool_def)

        return ",\n".join(tool_defs)

    def _generate_tool_handlers(self, tools: List[ToolDefinition]) -> str:
        """Generate switch case handlers"""
        handlers = []

        for tool in tools:
            handler = f"""            case '{tool.name}':
                return this.{self._to_camel_case(tool.name)}(args);"""
            handlers.append(handler)

        return "\n".join(handlers)

    def _generate_tool_implementations(self, tools: List[ToolDefinition]) -> str:
        """Generate tool implementation methods"""
        implementations = []

        for tool in tools:
            schema_name = (
                self._to_pascal_case(tool.name) + "Schema" if tool.parameters else None
            )

            type_annotation = f"z.infer<typeof {schema_name}>" if schema_name else "any"
            validation = (
                f"// Validate args\n            const validated = {schema_name}.parse(args);"
                if schema_name
                else ""
            )

            impl = f"""    private async {self._to_camel_case(tool.name)}(args: {type_annotation}) {{
        try {{
            {validation}

            // TODO: Implement {tool.name}

            return {{
                success: true,
                message: 'Successfully executed {tool.name}',
            }};
        }} catch (error) {{
            return {{
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
            }};
        }}
    }}"""
            implementations.append(impl)

        return "\n\n".join(implementations)

    def _generate_service_initialization(self, config: MCPConfig) -> str:
        """Generate service initialization code"""
        init_code = []

        if config.use_mock:
            if any("qdrant" in dep for dep in config.dependencies):
                init_code.append("this.qdrant = new MockQdrantClient();")
            if any("supabase" in dep for dep in config.dependencies):
                init_code.append(
                    """const supabaseUrl = process.env.SUPABASE_URL || 'http://localhost:54321';
        const supabaseKey = process.env.SUPABASE_SERVICE_KEY || 'mock-key';
        this.supabase = createClient(supabaseUrl, supabaseKey);"""
                )

        return (
            "\n        ".join(init_code)
            if init_code
            else "// No services to initialize"
        )

    def _generate_typescript_package(self, config: MCPConfig, server_dir: Path):
        """Generate package.json"""
        package = {
            "name": f"@elf-automations/{config.name}-mcp",
            "version": config.version,
            "description": config.description,
            "type": "module",
            "main": "server.js",
            "scripts": {
                "build": "tsc",
                "start": "node server.js",
                "dev": "tsx server.ts",
                "test": "jest",
            },
            "dependencies": {"@modelcontextprotocol/sdk": "^1.0.0", "zod": "^3.22.4"},
            "devDependencies": {
                "@types/node": "^20.10.5",
                "tsx": "^4.7.0",
                "typescript": "^5.3.3",
                "jest": "^29.7.0",
            },
        }

        # Add additional dependencies
        for dep in config.dependencies:
            # Parse dependency (could be package@version)
            parts = dep.split("@")
            if len(parts) == 2:
                package["dependencies"][f"@{parts[0]}"] = parts[1]
            elif len(parts) == 3:  # Scoped package
                package["dependencies"][f"@{parts[0]}@{parts[1]}"] = parts[2]
            else:
                package["dependencies"][dep] = "latest"

        with open(server_dir / "package.json", "w") as f:
            json.dump(package, f, indent=2)

    def _generate_typescript_config(self, config: MCPConfig, server_dir: Path):
        """Generate tsconfig.json"""
        tsconfig = {
            "extends": "../../../tsconfig.json",
            "compilerOptions": {"outDir": ".", "rootDir": "."},
            "include": ["server.ts", "mocks/**/*.ts"],
            "exclude": ["node_modules"],
        }

        with open(server_dir / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)

    def _generate_typescript_mocks(self, config: MCPConfig, server_dir: Path):
        """Generate mock implementations"""
        mocks_dir = server_dir / "mocks"
        mocks_dir.mkdir(exist_ok=True)

        # Generate mock for Qdrant if needed
        if any("qdrant" in dep for dep in config.dependencies):
            mock_code = """export class MockQdrantClient {
    private storage = new Map<string, any[]>();

    async upsert(collection: string, points: any[]) {
        if (!this.storage.has(collection)) {
            this.storage.set(collection, []);
        }
        const existing = this.storage.get(collection)!;
        points.forEach(point => {
            const index = existing.findIndex(p => p.id === point.id);
            if (index >= 0) {
                existing[index] = point;
            } else {
                existing.push(point);
            }
        });
    }

    async search(collection: string, query: any) {
        const points = this.storage.get(collection) || [];
        return points.slice(0, query.limit || 10);
    }

    async delete(collection: string, ids: string[]) {
        const points = this.storage.get(collection) || [];
        const filtered = points.filter(p => !ids.includes(p.id));
        this.storage.set(collection, filtered);
    }
}
"""
            with open(mocks_dir / "qdrant.ts", "w") as f:
                f.write(mock_code)

    def _generate_readme(self, config: MCPConfig, server_dir: Path):
        """Generate README.md"""
        readme = f"""# {config.display_name} MCP Server

{config.description}

## Complexity Level: {config.complexity.value.title()}

## Features

{self._format_tools_list(config.tools)}

{self._format_resources_list(config.resources)}

## Development Setup

```bash
npm install
npm run dev
```

## Environment Variables

{self._format_env_vars(config.environment)}

## Testing

```bash
npm test
```

## Production

```bash
npm run build
npm start
```
"""

        if config.use_mock:
            readme += """
## Mock Mode

This MCP includes mock implementations for development. Set `NODE_ENV=development` to use mocks.
"""

        if config.templates:
            readme += f"""
## Based on Templates

This MCP was created using the following templates:
{chr(10).join(f"- {t}" for t in config.templates)}
"""

        with open(server_dir / "README.md", "w") as f:
            f.write(readme)

    def _generate_config_json(self, config: MCPConfig, server_dir: Path):
        """Generate config.json for MCP metadata"""
        config_data = {
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "tools": [
                {"name": tool.name, "description": tool.description}
                for tool in config.tools
            ],
            "resources": [
                {"name": resource.name, "description": resource.description}
                for resource in config.resources
            ],
            "required_env": [
                k for k, v in config.environment.items() if v.startswith("${")
            ],
            "optional_env": [
                k for k, v in config.environment.items() if not v.startswith("${")
            ],
        }

        with open(server_dir / "config.json", "w") as f:
            json.dump(config_data, f, indent=2)

    def _generate_python_mcp(self, config: MCPConfig):
        """Generate Python MCP (simplified for now)"""
        # TODO: Implement Python generation similar to TypeScript
        self.console.print(
            "[yellow]Python MCP generation coming soon! For now, use TypeScript.[/yellow]"
        )

    # Utility methods
    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase"""
        return "".join(word.capitalize() for word in name.split("_"))

    def _to_camel_case(self, name: str) -> str:
        """Convert to camelCase"""
        words = name.split("_")
        return words[0] + "".join(word.capitalize() for word in words[1:])

    def _format_tools_list(self, tools: List[ToolDefinition]) -> str:
        """Format tools as markdown list"""
        if not tools:
            return "No tools defined."

        lines = ["### Tools\n"]
        for tool in tools:
            lines.append(f"- **`{tool.name}`**: {tool.description}")
            if tool.parameters:
                lines.append(f"  - Parameters: {', '.join(tool.parameters.keys())}")

        return "\n".join(lines)

    def _format_resources_list(self, resources: List[ResourceDefinition]) -> str:
        """Format resources as markdown list"""
        if not resources:
            return ""

        lines = ["### Resources\n"]
        for resource in resources:
            lines.append(f"- **`{resource.name}`**: {resource.description}")

        return "\n".join(lines)

    def _format_env_vars(self, env_vars: Dict[str, str]) -> str:
        """Format environment variables"""
        if not env_vars:
            return "No environment variables required."

        lines = []
        for key, value in env_vars.items():
            required = "Required" if value.startswith("${") else "Optional"
            lines.append(f"- `{key}`: {required}")

        return "\n".join(lines)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced MCP Factory - Create Model Context Protocol servers"
    )
    parser.add_argument("--list", action="store_true", help="List existing MCP servers")

    args = parser.parse_args()

    factory = MCPFactory()

    if args.list:
        # TODO: Implement listing
        console.print("[yellow]Listing functionality coming soon![/yellow]")
    else:
        factory.create_mcp()


if __name__ == "__main__":
    main()
