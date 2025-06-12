#!/usr/bin/env python3
"""
Simple test for distributed agent architecture without full A2A server setup.
Tests the core components and integration.
"""

import asyncio
import logging
import os
import sys

# Add the project root to Python path
sys.path.insert(0, "/Users/bryansparks/projects/ELFAutomations")

from agents.distributed.base.distributed_agent import (
    AgentConfig,
    DistributedCrewAIAgent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_distributed_simple")


class SimpleTestAgent(DistributedCrewAIAgent):
    """Simple test agent for validation."""

    async def handle_message(self, message):
        """Simple message handler for testing."""
        logger.info(f"Received message: {message}")
        return {"status": "received", "message_type": str(type(message))}


async def test_agent_creation():
    """Test basic agent creation and configuration."""
    logger.info("🔍 Testing agent creation...")

    config = AgentConfig(
        agent_id="test-simple-agent",
        role="Test Agent",
        goal="Test basic functionality",
        backstory="A simple test agent for validation",
        department="test",
        a2a_port=8081,
        service_name="test-agent-service",
    )

    agent = SimpleTestAgent(config)

    # Test agent card generation
    agent_card = agent.get_agent_card()
    assert agent_card.name == "Test Agent (test-simple-agent)"
    assert agent_card.version == "1.0.0"
    assert "test-agent-service:8081" in agent_card.url

    logger.info(f"✅ Agent card created: {agent_card.name}")

    # Test health status
    health = agent.get_health_status()
    assert "status" in health
    assert "timestamp" in health

    logger.info(f"✅ Health status: {health['status']}")

    # Test metrics
    metrics = agent.get_metrics()
    assert "agent_id" in metrics
    assert metrics["agent_id"] == "test-simple-agent"

    logger.info(f"✅ Metrics collected: {len(metrics)} fields")

    return True


async def test_crewai_integration():
    """Test CrewAI integration."""
    logger.info("🔍 Testing CrewAI integration...")

    config = AgentConfig(
        agent_id="test-crew-agent",
        role="CrewAI Test Agent",
        goal="Test CrewAI task execution",
        backstory="An agent for testing CrewAI integration",
        department="test",
    )

    agent = SimpleTestAgent(config)

    # Test task execution
    task_description = "Generate a simple greeting message"
    context = {"target": "distributed agent architecture"}

    result = await agent.execute_task(task_description, context)

    assert result["status"] == "completed"
    assert "result" in result
    assert result["agent_id"] == "test-crew-agent"

    logger.info(f"✅ Task executed successfully: {result['result'][:50]}...")

    return True


async def test_discovery_integration():
    """Test discovery service integration."""
    logger.info("🔍 Testing discovery integration...")

    from agents.distributed.a2a.discovery import DiscoveryService

    # Test local discovery (no external endpoint)
    discovery = DiscoveryService()

    config = AgentConfig(
        agent_id="test-discovery-agent",
        role="Discovery Test Agent",
        goal="Test discovery functionality",
        backstory="An agent for testing discovery",
        department="test",
    )

    agent = SimpleTestAgent(config)
    agent_card = agent.get_agent_card()

    # Test registration
    success = await discovery.register_agent(agent_card)
    assert success, "Agent registration failed"

    logger.info("✅ Agent registered with discovery service")

    # Test discovery
    agents = await discovery.discover_agents()
    assert len(agents) > 0, "No agents found in discovery"

    found_agent = next((a for a in agents if "Discovery Test Agent" in a.name), None)
    assert found_agent is not None, "Registered agent not found in discovery"

    logger.info(f"✅ Agent discovered: {found_agent.name}")

    # Test unregistration
    # Note: We'll use the agent name as identifier since agent_id is not in the new structure
    success = await discovery.unregister_agent("test-discovery-agent")
    assert success, "Agent unregistration failed"

    logger.info("✅ Agent unregistered from discovery service")

    return True


async def main():
    """Run all tests."""
    logger.info("🚀 Starting Distributed Agent Architecture Tests")

    try:
        # Test basic agent creation
        await test_agent_creation()

        # Test CrewAI integration
        await test_crewai_integration()

        # Test discovery integration
        await test_discovery_integration()

        logger.info("🎉 All distributed agent tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)
