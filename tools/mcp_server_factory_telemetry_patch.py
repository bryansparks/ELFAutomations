#!/usr/bin/env python3
"""
Telemetry patch for mcp_server_factory.py
Adds telemetry and unified registry integration to the MCP server factory
"""

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from elf_automations.shared.telemetry import telemetry_client


def patch_mcp_server_factory():
    """Patch the MCP server factory to add telemetry and registration"""

    # Import the MCP server factory
    try:
        from mcp_server_factory import MCPServerFactory
    except ImportError:
        print("Error: Could not import MCP server factory")
        return False

    # Store original methods
    original_create_server = MCPServerFactory.create_server
    original_deploy_server = (
        MCPServerFactory.deploy_server
        if hasattr(MCPServerFactory, "deploy_server")
        else None
    )

    def create_server_with_telemetry(
        self,
        name: str,
        display_name: str,
        description: str,
        template: str = "tool-focused",
        **kwargs,
    ) -> Dict[str, Any]:
        """Enhanced create_server with telemetry"""
        start_time = telemetry_client.start_timer()
        server_id = f"mcp-{name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        correlation_id = str(uuid.uuid4())

        try:
            # Call original method
            result = original_create_server(
                self, name, display_name, description, template, **kwargs
            )

            # Extract tools and resources from result
            tools = []
            resources = []
            if "tools" in kwargs:
                tools = [
                    tool.get("name", "unknown") for tool in kwargs.get("tools", [])
                ]
            if "resources" in kwargs:
                resources = [
                    res.get("name", "unknown") for res in kwargs.get("resources", [])
                ]

            # Record success telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            telemetry_client.record_n8n(
                workflow_id="mcp-factory",
                workflow_name="MCP Server Factory",
                node_name="create_server",
                target_service="filesystem",
                operation="create_mcp_server",
                status="success",
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                metadata={
                    "server_id": server_id,
                    "server_name": name,
                    "display_name": display_name,
                    "template": template,
                    "tool_count": len(tools),
                    "resource_count": len(resources),
                    "tools": tools[:5],  # First 5 tools for metadata
                    "resources": resources[:5],  # First 5 resources
                },
            )

            # Register in unified registry if Supabase is available
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
                try:
                    from supabase import create_client

                    client = create_client(
                        os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY")
                    )

                    # Build capabilities list
                    capabilities = []
                    if tools:
                        capabilities.extend([f"tool:{tool}" for tool in tools])
                    if resources:
                        capabilities.extend([f"resource:{res}" for res in resources])
                    if not capabilities:
                        capabilities = ["mcp_server", template]

                    # Register MCP server in unified registry
                    registry_data = {
                        "p_entity_id": server_id,
                        "p_entity_type": "mcp_server",
                        "p_entity_name": display_name,
                        "p_registered_by": "mcp_server_factory",
                        "p_metadata": {
                            "name": name,
                            "description": description,
                            "template": template,
                            "tool_count": len(tools),
                            "resource_count": len(resources),
                            "created_at": datetime.utcnow().isoformat(),
                        },
                        "p_capabilities": capabilities[:20],  # Limit to 20 capabilities
                        "p_endpoint_url": f"http://{name}:8095",  # Standard MCP port
                        "p_parent_entity_id": kwargs.get("parent_id"),
                    }

                    client.rpc("register_entity", registry_data).execute()

                    # Update state to created
                    client.rpc(
                        "update_entity_state",
                        {
                            "p_entity_id": server_id,
                            "p_entity_type": "mcp_server",
                            "p_new_state": "created",
                            "p_health_status": "unknown",
                            "p_updated_by": "mcp_server_factory",
                            "p_reason": "MCP server created successfully",
                        },
                    ).execute()

                except Exception as e:
                    print(
                        f"Warning: Could not register MCP server in unified registry: {e}"
                    )

            # Add server_id to result
            result["server_id"] = server_id
            return result

        except Exception as e:
            # Record error telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            telemetry_client.record_n8n(
                workflow_id="mcp-factory",
                workflow_name="MCP Server Factory",
                node_name="create_server",
                target_service="filesystem",
                operation="create_mcp_server",
                status="error",
                duration_ms=duration_ms,
                error_message=str(e),
                correlation_id=correlation_id,
                metadata={
                    "server_name": name,
                    "template": template,
                },
            )
            raise

    def deploy_server_with_telemetry(
        self, server_path: Path, environment: str = "development"
    ) -> bool:
        """Enhanced deploy_server with telemetry"""
        if not original_deploy_server:
            return False

        start_time = telemetry_client.start_timer()
        correlation_id = str(uuid.uuid4())
        server_name = server_path.name

        try:
            # Call original method
            result = original_deploy_server(self, server_path, environment)

            # Record deployment telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            telemetry_client.record_n8n(
                workflow_id="mcp-factory",
                workflow_name="MCP Server Factory",
                node_name="deploy_server",
                target_service="kubernetes",
                operation="deploy_mcp_server",
                status="success" if result else "failed",
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                metadata={
                    "server_name": server_name,
                    "environment": environment,
                    "deployed": result,
                },
            )

            # Update registry state if deployed
            if result and os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
                try:
                    from supabase import create_client

                    client = create_client(
                        os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY")
                    )

                    # Find server ID by name
                    response = (
                        client.table("unified_registry")
                        .select("entity_id")
                        .eq("entity_name", server_name)
                        .eq("entity_type", "mcp_server")
                        .execute()
                    )

                    if response.data:
                        server_id = response.data[0]["entity_id"]

                        # Update state to deployed
                        client.rpc(
                            "update_entity_state",
                            {
                                "p_entity_id": server_id,
                                "p_entity_type": "mcp_server",
                                "p_new_state": "deployed",
                                "p_health_status": "healthy",
                                "p_updated_by": "mcp_server_factory",
                                "p_reason": f"Deployed to {environment}",
                            },
                        ).execute()

                except Exception as e:
                    print(
                        f"Warning: Could not update MCP server state in registry: {e}"
                    )

            return result

        except Exception as e:
            # Record error telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            telemetry_client.record_n8n(
                workflow_id="mcp-factory",
                workflow_name="MCP Server Factory",
                node_name="deploy_server",
                target_service="kubernetes",
                operation="deploy_mcp_server",
                status="error",
                duration_ms=duration_ms,
                error_message=str(e),
                correlation_id=correlation_id,
                metadata={
                    "server_name": server_name,
                    "environment": environment,
                },
            )
            raise

    # Patch the methods
    MCPServerFactory.create_server = create_server_with_telemetry
    if original_deploy_server:
        MCPServerFactory.deploy_server = deploy_server_with_telemetry

    print("✅ MCP server factory patched with telemetry and registration")
    return True


def add_telemetry_to_mcp_templates():
    """Add telemetry client import to generated MCP server files"""

    python_template_addition = '''
# Telemetry imports (added by factory)
try:
    from elf_automations.shared.telemetry import telemetry_client
    TELEMETRY_ENABLED = True
except ImportError:
    print("Warning: Telemetry not available")
    TELEMETRY_ENABLED = False

# MCP tool telemetry wrapper
def track_tool_usage(tool_name: str):
    """Decorator to track MCP tool usage"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if TELEMETRY_ENABLED:
                start_time = telemetry_client.start_timer()

            try:
                result = await func(*args, **kwargs)

                if TELEMETRY_ENABLED:
                    await telemetry_client.record_mcp(
                        source_id="mcp-server",
                        mcp_name=SERVER_NAME,
                        tool_name=tool_name,
                        status="success",
                        duration_ms=telemetry_client.calculate_duration_ms(start_time)
                    )

                return result

            except Exception as e:
                if TELEMETRY_ENABLED:
                    await telemetry_client.record_mcp(
                        source_id="mcp-server",
                        mcp_name=SERVER_NAME,
                        tool_name=tool_name,
                        status="error",
                        duration_ms=telemetry_client.calculate_duration_ms(start_time),
                        error_message=str(e)
                    )
                raise

        return wrapper
    return decorator
'''

    typescript_template_addition = """
// Telemetry imports (added by factory)
import { TelemetryClient } from '@elf-automations/telemetry';

const telemetryClient = new TelemetryClient();
const SERVER_NAME = process.env.MCP_SERVER_NAME || 'unknown';

// MCP tool telemetry wrapper
export function trackToolUsage(toolName: string) {
    return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
        const originalMethod = descriptor.value;

        descriptor.value = async function (...args: any[]) {
            const startTime = Date.now();

            try {
                const result = await originalMethod.apply(this, args);

                await telemetryClient.recordMCP({
                    sourceId: 'mcp-server',
                    mcpName: SERVER_NAME,
                    toolName: toolName,
                    status: 'success',
                    durationMs: Date.now() - startTime
                });

                return result;

            } catch (error) {
                await telemetryClient.recordMCP({
                    sourceId: 'mcp-server',
                    mcpName: SERVER_NAME,
                    toolName: toolName,
                    status: 'error',
                    durationMs: Date.now() - startTime,
                    errorMessage: error.message
                });

                throw error;
            }
        };

        return descriptor;
    };
}
"""

    print("📝 Telemetry templates configured for MCP servers")
    return {
        "python": python_template_addition,
        "typescript": typescript_template_addition,
    }


if __name__ == "__main__":
    print("🔧 Patching MCP Server Factory with Telemetry...")

    # Patch the factory
    if patch_mcp_server_factory():
        print("\n📋 MCP Server Factory Telemetry Integration Complete!")
        print("\nFeatures added:")
        print("  - Telemetry tracking for server creation")
        print("  - Telemetry tracking for server deployment")
        print("  - Automatic registration in unified registry")
        print("  - Tool and resource capability tracking")
        print("  - State tracking for deployed servers")
        print("  - Tool usage telemetry decorators")

        print("\n🔄 Next steps:")
        print("  1. Import this patch in mcp_server_factory.py")
        print("  2. MCP servers will include telemetry decorators")
        print("  3. All server operations will be tracked")
        print("  4. Tool usage within servers can be monitored")
    else:
        print("❌ Failed to patch MCP server factory")
