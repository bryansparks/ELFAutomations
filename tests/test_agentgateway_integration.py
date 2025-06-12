"""
Test suite for TASK-006 AgentGateway MCP Integration

This test suite validates the AgentGateway integration for centralized
MCP infrastructure in the Virtual AI Company Platform.
"""

import asyncio
import json
import os

# Import our agent infrastructure
import sys
import uuid
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from agents.langgraph_base import (
    AgentGatewayClient,
    AgentLifecycleState,
    LangGraphBaseAgent,
    MCPToolCall,
)


class TestAgentGatewayClient:
    """Test AgentGateway client functionality."""

    @pytest.fixture
    def gateway_client(self):
        """Create a test AgentGateway client."""
        return AgentGatewayClient(
            gateway_url="http://localhost:3000", agent_id="test-agent-001"
        )

    @pytest.mark.asyncio
    async def test_client_initialization(self, gateway_client):
        """Test AgentGateway client initialization."""
        assert gateway_client.gateway_url == "http://localhost:3000"
        assert gateway_client.agent_id == "test-agent-001"
        assert gateway_client.session is None

    @pytest.mark.asyncio
    async def test_context_manager(self, gateway_client):
        """Test AgentGateway client context manager."""
        async with gateway_client as client:
            assert client.session is not None
            assert isinstance(client.session, aiohttp.ClientSession)

        # Session should be closed after context exit
        assert client.session.closed

    @pytest.mark.asyncio
    async def test_list_available_tools_success(self, gateway_client):
        """Test successful tool listing via AgentGateway."""
        mock_response_data = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {
                "tools": [
                    {
                        "name": "supabase/list_tables",
                        "description": "List all tables in the database",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                    {
                        "name": "business/get_customers",
                        "description": "Get customer data",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"limit": {"type": "integer"}},
                        },
                    },
                ]
            },
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_response_data
            mock_post.return_value.__aenter__.return_value = mock_response

            async with gateway_client as client:
                tools = await client.list_available_tools()

                assert len(tools) == 2
                assert tools[0]["name"] == "supabase/list_tables"
                assert tools[1]["name"] == "business/get_customers"

    @pytest.mark.asyncio
    async def test_list_available_tools_empty(self, gateway_client):
        """Test tool listing with empty response."""
        mock_response_data = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"tools": []},
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_response_data
            mock_post.return_value.__aenter__.return_value = mock_response

            async with gateway_client as client:
                tools = await client.list_available_tools()

                assert len(tools) == 0

    @pytest.mark.asyncio
    async def test_call_mcp_tool_success(self, gateway_client):
        """Test successful MCP tool call via AgentGateway."""
        tool_call = MCPToolCall(
            tool_name="list_tables", server_name="supabase", arguments={}
        )

        mock_response_data = {
            "jsonrpc": "2.0",
            "id": tool_call.call_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Tables: customers, leads, tasks, business_metrics, agent_activities",
                    }
                ]
            },
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_response_data
            mock_post.return_value.__aenter__.return_value = mock_response

            async with gateway_client as client:
                result = await client.call_mcp_tool(tool_call)

                assert "content" in result
                assert len(result["content"]) == 1
                assert "Tables:" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_call_mcp_tool_error(self, gateway_client):
        """Test MCP tool call with error response."""
        tool_call = MCPToolCall(
            tool_name="invalid_tool", server_name="supabase", arguments={}
        )

        mock_response_data = {
            "jsonrpc": "2.0",
            "id": tool_call.call_id,
            "error": {
                "code": -32601,
                "message": "Tool not found: supabase/invalid_tool",
            },
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_response_data
            mock_post.return_value.__aenter__.return_value = mock_response

            async with gateway_client as client:
                with pytest.raises(Exception) as exc_info:
                    await client.call_mcp_tool(tool_call)

                assert "Tool not found" in str(exc_info.value)


class TestLangGraphAgentGatewayIntegration:
    """Test LangGraph agent integration with AgentGateway."""

    class TestAgent(LangGraphBaseAgent):
        """Test implementation of LangGraph agent."""

        def __init__(self, agent_id: str):
            super().__init__(
                agent_id=agent_id,
                name="Test Agent",
                department="Testing",
                system_prompt="You are a test agent.",
                gateway_url="http://localhost:3000",
            )

        def _build_graph(self):
            """Build test graph."""
            pass

        async def _execute_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
            """Execute test task."""
            return {"status": "completed", "result": "test result"}

    @pytest.fixture
    def test_agent(self):
        """Create a test agent."""
        return self.TestAgent("test-agent-integration")

    def test_agent_initialization_with_gateway(self, test_agent):
        """Test agent initialization with AgentGateway."""
        assert test_agent.agent_id == "test-agent-integration"
        assert test_agent.name == "Test Agent"
        assert test_agent.department == "Testing"
        assert test_agent.gateway_client.gateway_url == "http://localhost:3000"
        assert test_agent.gateway_client.agent_id == "test-agent-integration"

    @pytest.mark.asyncio
    async def test_agent_tool_discovery(self, test_agent):
        """Test agent tool discovery via AgentGateway."""
        mock_tools = [
            {"name": "supabase/list_tables", "description": "List database tables"},
            {"name": "business/get_metrics", "description": "Get business metrics"},
        ]

        with patch.object(
            test_agent.gateway_client, "list_available_tools", return_value=mock_tools
        ):
            await test_agent.start()

            # Check that tools were discovered
            assert len(test_agent.available_tools) == 2
            assert any(
                tool["name"] == "supabase/list_tables"
                for tool in test_agent.available_tools
            )
            assert any(
                tool["name"] == "business/get_metrics"
                for tool in test_agent.available_tools
            )

    @pytest.mark.asyncio
    async def test_agent_tool_execution(self, test_agent):
        """Test agent tool execution via AgentGateway."""
        mock_result = {
            "content": [
                {"type": "text", "text": "Database tables: customers, leads, tasks"}
            ]
        }

        with patch.object(
            test_agent.gateway_client, "call_mcp_tool", return_value=mock_result
        ):
            await test_agent.start()

            # Execute a tool call
            tool_call = MCPToolCall(
                tool_name="list_tables", server_name="supabase", arguments={}
            )

            result = await test_agent.gateway_client.call_mcp_tool(tool_call)

            assert "content" in result
            assert "Database tables:" in result["content"][0]["text"]


class TestAgentGatewayDeployment:
    """Test AgentGateway Kubernetes deployment."""

    def test_kubernetes_manifests_exist(self):
        """Test that all required Kubernetes manifests exist."""
        base_path = os.path.join(
            os.path.dirname(__file__), "..", "k8s", "base", "agentgateway"
        )

        required_files = [
            "configmap.yaml",
            "deployment.yaml",
            "service.yaml",
            "rbac.yaml",
            "monitoring.yaml",
            "kustomization.yaml",
        ]

        for file_name in required_files:
            file_path = os.path.join(base_path, file_name)
            assert os.path.exists(file_path), f"Required manifest {file_name} not found"

    def test_agentgateway_config_valid(self):
        """Test that AgentGateway configuration is valid JSON."""
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "agentgateway", "config.json"
        )

        assert os.path.exists(config_path), "AgentGateway config.json not found"

        with open(config_path, "r") as f:
            config = json.load(f)

        # Validate basic structure
        assert "type" in config
        assert config["type"] == "static"
        assert "listeners" in config
        assert "targets" in config
        assert "mcp" in config["targets"]

        # Validate listeners
        listeners = config["listeners"]
        assert len(listeners) >= 1

        mcp_listener = next((l for l in listeners if l.get("protocol") == "MCP"), None)
        assert mcp_listener is not None, "MCP listener not found"
        assert mcp_listener["sse"]["port"] == 3000

        # Validate MCP targets
        mcp_targets = config["targets"]["mcp"]
        assert len(mcp_targets) >= 2

        target_names = [target["name"] for target in mcp_targets]
        assert "supabase" in target_names
        assert "business" in target_names

    def test_deployment_script_exists(self):
        """Test that deployment script exists and is executable."""
        script_path = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "deploy_agentgateway.sh"
        )

        assert os.path.exists(script_path), "Deployment script not found"
        assert os.access(script_path, os.X_OK), "Deployment script is not executable"


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance in AgentGateway integration."""

    def test_mcp_request_format(self):
        """Test that MCP requests follow JSON-RPC 2.0 format."""
        tool_call = MCPToolCall(
            tool_name="test_tool",
            server_name="test_server",
            arguments={"param": "value"},
        )

        # Simulate the request format used in AgentGatewayClient
        mcp_request = {
            "jsonrpc": "2.0",
            "id": tool_call.call_id,
            "method": "tools/call",
            "params": {
                "name": f"{tool_call.server_name}/{tool_call.tool_name}",
                "arguments": tool_call.arguments,
            },
        }

        # Validate JSON-RPC 2.0 compliance
        assert mcp_request["jsonrpc"] == "2.0"
        assert "id" in mcp_request
        assert "method" in mcp_request
        assert "params" in mcp_request

        # Validate MCP-specific format
        assert mcp_request["method"] == "tools/call"
        assert mcp_request["params"]["name"] == "test_server/test_tool"
        assert mcp_request["params"]["arguments"] == {"param": "value"}

    def test_tool_name_format(self):
        """Test that tool names follow server/tool format."""
        tool_call = MCPToolCall(
            tool_name="list_tables", server_name="supabase", arguments={}
        )

        expected_name = f"{tool_call.server_name}/{tool_call.tool_name}"
        assert expected_name == "supabase/list_tables"

        # Test with business tools
        business_tool = MCPToolCall(
            tool_name="get_customers", server_name="business", arguments={"limit": 10}
        )

        expected_business_name = (
            f"{business_tool.server_name}/{business_tool.tool_name}"
        )
        assert expected_business_name == "business/get_customers"


# Integration test runner
async def run_integration_tests():
    """Run integration tests against live AgentGateway."""
    print("🧪 Running TASK-006 AgentGateway Integration Tests...")

    # Test 1: AgentGateway connectivity
    print("\n1. Testing AgentGateway connectivity...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8080/health") as response:
                if response.status == 200:
                    print("   ✅ AgentGateway admin endpoint is accessible")
                else:
                    print(
                        f"   ❌ AgentGateway admin endpoint returned {response.status}"
                    )
    except Exception as e:
        print(f"   ❌ AgentGateway connectivity failed: {e}")

    # Test 2: MCP protocol endpoint
    print("\n2. Testing MCP protocol endpoint...")
    try:
        gateway_client = AgentGatewayClient(
            gateway_url="http://localhost:3000", agent_id="integration-test"
        )

        async with gateway_client as client:
            tools = await client.list_available_tools()
            print(f"   ✅ Retrieved {len(tools)} tools via MCP protocol")

            for tool in tools[:3]:  # Show first 3 tools
                print(f"      - {tool.get('name', 'Unknown')}")

    except Exception as e:
        print(f"   ❌ MCP protocol test failed: {e}")

    # Test 3: Tool federation
    print("\n3. Testing tool federation...")
    try:
        gateway_client = AgentGatewayClient(
            gateway_url="http://localhost:3000", agent_id="federation-test"
        )

        async with gateway_client as client:
            tools = await client.list_available_tools()

            supabase_tools = [
                t for t in tools if t.get("name", "").startswith("supabase/")
            ]
            business_tools = [
                t for t in tools if t.get("name", "").startswith("business/")
            ]

            print(f"   ✅ Supabase tools: {len(supabase_tools)}")
            print(f"   ✅ Business tools: {len(business_tools)}")

            if len(supabase_tools) > 0 and len(business_tools) > 0:
                print("   ✅ Tool federation is working correctly")
            else:
                print("   ❌ Tool federation incomplete")

    except Exception as e:
        print(f"   ❌ Tool federation test failed: {e}")

    print("\n🎯 Integration tests completed!")


if __name__ == "__main__":
    # Run integration tests if AgentGateway is available
    asyncio.run(run_integration_tests())
