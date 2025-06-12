"""
Test Suite for TASK-005: Agent Infrastructure Foundation

This test suite validates the foundational agent infrastructure using:
- LangGraph for stateful workflows
- kagent for Kubernetes deployment
- MCP via agentgateway.dev for tool access

Tests ensure the pattern is correctly established for all future agents.
"""

import asyncio
import os
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from agents.demo_agent import DemoAgent, create_demo_agent

# Import our foundation components
from agents.langgraph_base import (
    AgentGatewayClient,
    AgentLifecycleState,
    LangGraphBaseAgent,
)


class TestLangGraphFoundation:
    """Test the LangGraph foundation implementation."""

    @pytest.fixture
    def mock_gateway_client(self):
        """Mock AgentGatewayClient for testing."""
        client = Mock(spec=AgentGatewayClient)
        client.get_available_tools = AsyncMock(
            return_value=[
                {"name": "get_customers", "server": "business_tools"},
                {"name": "execute_sql", "server": "supabase"},
            ]
        )
        client.call_tool = AsyncMock(return_value={"result": "success"})
        return client

    @pytest.fixture
    def demo_agent(self, mock_gateway_client):
        """Create a demo agent for testing."""
        with patch(
            "agents.langgraph_base.AgentGatewayClient", return_value=mock_gateway_client
        ):
            agent = DemoAgent(
                agent_id="test-demo-agent",
                gateway_url="https://test.agentgateway.dev",
                gateway_api_key="test-key",
            )
            return agent

    def test_agent_initialization(self, demo_agent):
        """Test that agents initialize with correct configuration."""
        assert demo_agent.agent_id == "test-demo-agent"
        assert demo_agent.name == "Demo Agent"
        assert demo_agent.department == "demonstration"
        assert demo_agent.state == AgentLifecycleState.CREATED
        assert "LangGraph" in demo_agent.system_prompt
        assert "agentgateway" in demo_agent.system_prompt

    @pytest.mark.asyncio
    async def test_agent_lifecycle(self, demo_agent):
        """Test agent lifecycle management."""
        # Test start
        await demo_agent.start()
        assert demo_agent.state == AgentLifecycleState.RUNNING

        # Test health check
        health = demo_agent.get_health_check()
        assert health.agent_id == "test-demo-agent"
        assert health.status == AgentLifecycleState.RUNNING
        assert health.uptime_seconds >= 0

        # Test stop
        await demo_agent.stop()
        assert demo_agent.state == AgentLifecycleState.STOPPED

    @pytest.mark.asyncio
    async def test_langgraph_workflow(self, demo_agent):
        """Test LangGraph workflow execution."""
        await demo_agent.start()

        # Mock the LLM response
        with patch("agents.langgraph_base.ChatAnthropic") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(
                return_value=Mock(content="Test response from LangGraph workflow")
            )

            result = await demo_agent.process_message("Test message")

            assert "messages" in result
            assert len(result["messages"]) > 0

        await demo_agent.stop()

    @pytest.mark.asyncio
    async def test_mcp_integration_via_gateway(self, demo_agent, mock_gateway_client):
        """Test MCP integration through agentgateway."""
        await demo_agent.start()

        # Test tool loading
        tools = await demo_agent.gateway_client.get_available_tools()
        assert len(tools) == 2
        assert any(tool["name"] == "get_customers" for tool in tools)
        assert any(tool["server"] == "supabase" for tool in tools)

        # Test tool execution
        result = await demo_agent.gateway_client.call_tool(
            "get_customers", {"limit": 10}
        )
        assert result["result"] == "success"

        await demo_agent.stop()

    def test_factory_function(self):
        """Test the agent factory function."""
        with patch("agents.langgraph_base.AgentGatewayClient"):
            agent = create_demo_agent(
                agent_id="factory-test", gateway_url="https://test.gateway.dev"
            )
            assert agent.agent_id == "factory-test"
            assert isinstance(agent, DemoAgent)


class TestKagentIntegration:
    """Test kagent Kubernetes integration."""

    def test_kagent_crd_structure(self):
        """Test the kagent CRD structure."""
        crd_path = "/Users/bryansparks/projects/ELFAutomations/k8s/base/kagent-langgraph-crd.yaml"

        with open(crd_path, "r") as f:
            crd_docs = list(yaml.safe_load_all(f))

        # Find the CRD document
        crd = next(
            doc for doc in crd_docs if doc.get("kind") == "CustomResourceDefinition"
        )

        # Validate CRD structure
        assert crd["metadata"]["name"] == "langgraphagents.kagent.io"
        assert crd["spec"]["group"] == "kagent.io"

        # Validate required fields
        spec_props = crd["spec"]["versions"][0]["schema"]["openAPIV3Schema"][
            "properties"
        ]["spec"]["properties"]
        required_fields = crd["spec"]["versions"][0]["schema"]["openAPIV3Schema"][
            "properties"
        ]["spec"]["required"]

        assert "agentGateway" in required_fields
        assert "agentClass" in required_fields
        assert "department" in required_fields

        # Validate agentGateway configuration
        gateway_config = spec_props["agentGateway"]["properties"]
        assert "url" in gateway_config
        assert gateway_config["url"]["default"] == "https://agentgateway.dev"

    def test_demo_agent_manifest(self):
        """Test the demo agent Kubernetes manifest."""
        manifest_path = (
            "/Users/bryansparks/projects/ELFAutomations/k8s/staging/demo-agent.yaml"
        )

        with open(manifest_path, "r") as f:
            docs = list(yaml.safe_load_all(f))

        # Find the LangGraphAgent resource
        agent_resource = next(
            doc for doc in docs if doc.get("kind") == "LangGraphAgent"
        )

        # Validate mandatory fields
        spec = agent_resource["spec"]
        assert spec["department"] == "demonstration"
        assert spec["agentClass"] == "agents.demo_agent.DemoAgent"
        assert spec["agentGateway"]["url"] == "https://agentgateway.dev"

        # Validate MCP tools configuration
        assert "mcpTools" in spec
        assert len(spec["mcpTools"]) >= 1

        # Find business_tools server
        business_tools = next(
            server
            for server in spec["mcpTools"]
            if server["serverName"] == "business_tools"
        )
        assert "get_customers" in business_tools["tools"]
        assert business_tools["priority"] == 1


class TestAgentGatewayIntegration:
    """Test agentgateway.dev integration."""

    @pytest.fixture
    def gateway_client(self):
        """Create a gateway client for testing."""
        return AgentGatewayClient(
            agent_id="test-agent",
            gateway_url="https://test.agentgateway.dev",
            api_key="test-key",
        )

    @pytest.mark.asyncio
    async def test_gateway_client_initialization(self, gateway_client):
        """Test gateway client initialization."""
        assert gateway_client.gateway_url == "https://test.agentgateway.dev"
        assert gateway_client.api_key == "test-key"
        assert gateway_client.agent_id == "test-agent"

    @pytest.mark.asyncio
    async def test_tool_discovery(self, gateway_client):
        """Test MCP tool discovery through gateway."""
        async with gateway_client:
            with patch("aiohttp.ClientSession.get") as mock_get:
                mock_response = Mock()
                mock_response.json = AsyncMock(
                    return_value={
                        "tools": [
                            {"name": "get_customers", "server": "business_tools"},
                            {"name": "execute_sql", "server": "supabase"},
                        ]
                    }
                )
                mock_response.status = 200
                mock_response.raise_for_status = Mock()
                mock_get.return_value.__aenter__.return_value = mock_response

                tools = await gateway_client.list_available_tools()
                assert len(tools) == 2
                assert tools[0]["name"] == "get_customers"

    @pytest.mark.asyncio
    async def test_tool_execution(self, gateway_client):
        """Test MCP tool execution through gateway."""
        from agents.langgraph_base import MCPToolCall

        async with gateway_client:
            with patch("aiohttp.ClientSession.post") as mock_post:
                mock_response = Mock()
                mock_response.json = AsyncMock(
                    return_value={
                        "result": {"customers": [{"id": 1, "name": "Test Customer"}]}
                    }
                )
                mock_response.status = 200
                mock_response.raise_for_status = Mock()
                mock_post.return_value.__aenter__.return_value = mock_response

                tool_call = MCPToolCall(
                    tool_name="get_customers",
                    server_name="business_tools",
                    arguments={"limit": 1},
                )
                result = await gateway_client.call_mcp_tool(tool_call)
                assert "result" in result
                assert "customers" in result["result"]


class TestTechnologyStackCompliance:
    """Test compliance with the mandatory technology stack."""

    def test_langgraph_dependency(self):
        """Test that LangGraph is properly configured."""
        # Check requirements.txt
        requirements_path = (
            "/Users/bryansparks/projects/ELFAutomations/requirements.txt"
        )
        with open(requirements_path, "r") as f:
            requirements = f.read()

        assert "langgraph" in requirements
        assert "langchain" in requirements

    def test_kagent_crd_exists(self):
        """Test that kagent CRD is properly defined."""
        crd_path = "/Users/bryansparks/projects/ELFAutomations/k8s/base/kagent-langgraph-crd.yaml"
        assert os.path.exists(crd_path)

        with open(crd_path, "r") as f:
            content = f.read()

        # Verify kagent integration
        assert "kagent.io" in content
        assert "LangGraphAgent" in content

    def test_mcp_protocol_compliance(self):
        """Test MCP protocol compliance."""
        # Verify agentgateway integration in base agent
        base_agent_path = (
            "/Users/bryansparks/projects/ELFAutomations/agents/langgraph_base.py"
        )
        with open(base_agent_path, "r") as f:
            content = f.read()

        assert "AgentGatewayClient" in content
        assert "agentgateway" in content
        assert "mcp" in content.lower()

    def test_agentgateway_mandatory_usage(self):
        """Test that agentgateway is mandatory for MCP access."""
        # Check that direct MCP connections are not allowed
        demo_agent_path = (
            "/Users/bryansparks/projects/ELFAutomations/agents/demo_agent.py"
        )
        with open(demo_agent_path, "r") as f:
            content = f.read()

        # Should use agentgateway, not direct MCP
        assert "agentgateway" in content
        # Should not have direct MCP server connections
        assert "mcp_server" not in content.lower()
        assert "direct_mcp" not in content.lower()


class TestInfrastructureValidation:
    """Test infrastructure validation and monitoring."""

    @pytest.mark.asyncio
    async def test_demo_agent_validation(self):
        """Test the demo agent infrastructure validation."""
        with patch("agents.langgraph_base.AgentGatewayClient"):
            agent = create_demo_agent()

            # Mock successful validation
            with patch.object(agent, "process_message") as mock_process:
                mock_process.return_value = {"messages": ["validation successful"]}

                validation = await agent.validate_infrastructure()

                # Should test all components
                assert "langgraph_workflow" in validation
                assert "mcp_connectivity" in validation
                assert "agentgateway_access" in validation
                assert "kagent_lifecycle" in validation
                assert "overall_status" in validation

    def test_health_check_implementation(self):
        """Test health check implementation."""
        with patch("agents.langgraph_base.AgentGatewayClient"):
            agent = create_demo_agent()

            health = agent.get_health_check()
            assert hasattr(health, "agent_id")
            assert hasattr(health, "status")
            assert hasattr(health, "uptime_seconds")
            assert hasattr(health, "error_count")


# Integration test to run the demo
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_demo_integration():
    """Integration test running the full demo."""
    with patch("agents.langgraph_base.AgentGatewayClient"):
        # This would run the actual demo if we had real services
        # For now, just test that the demo can be imported and initialized
        from agents.demo_agent import main

        # Mock the async main function
        with patch("agents.demo_agent.DemoAgent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.start = AsyncMock()
            mock_agent.stop = AsyncMock()
            mock_agent.demonstrate_workflow = AsyncMock(return_value={"messages": []})
            mock_agent.test_mcp_integration = AsyncMock(
                return_value={"available_tools": []}
            )
            mock_agent.validate_infrastructure = AsyncMock(
                return_value={"overall_status": "passed"}
            )
            mock_agent.get_health_check = Mock(
                return_value=Mock(
                    agent_id="test",
                    status=AgentLifecycleState.RUNNING,
                    uptime_seconds=10.0,
                    error_count=0,
                )
            )
            mock_agent.__str__ = Mock(return_value="Demo Agent")

            mock_agent_class.return_value = mock_agent

            # This should run without errors
            await main()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
