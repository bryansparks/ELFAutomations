"""
Test script for distributed CrewAI + A2A agents.
Demonstrates the new architecture with independent agent deployment.
"""

import asyncio
import logging
import sys
from datetime import datetime

from ..a2a.messages import MessagePriority, create_task_request
from ..base import AgentConfig
from .sales_agent import SalesAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_distributed_agent")


async def test_sales_agent():
    """Test the distributed sales agent."""
    logger.info("🚀 Testing Distributed CrewAI + A2A Sales Agent")

    # Create agent configuration
    config = AgentConfig(
        agent_id="test-sales-agent",
        role="Senior Sales Development Representative",
        goal="Test lead qualification and outreach capabilities",
        backstory="Test agent for validating distributed architecture",
        department="sales",
        a2a_port=8081,
        service_name="test-sales-agent-service",
    )

    # Initialize sales agent
    sales_agent = SalesAgent(config)

    try:
        # Start the agent
        logger.info("Starting sales agent...")
        await sales_agent.start()

        # Test basic functionality
        await test_agent_health(sales_agent)
        await test_task_execution(sales_agent)
        await test_lead_qualification(sales_agent)
        await test_cold_outreach(sales_agent)
        await test_metrics(sales_agent)

        logger.info("✅ All tests passed!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
    finally:
        # Stop the agent
        logger.info("Stopping sales agent...")
        await sales_agent.stop()


async def test_agent_health(agent: SalesAgent):
    """Test agent health checks."""
    logger.info("🔍 Testing agent health...")

    # Check health status
    health_status = agent.get_health_status()
    assert health_status["status"] in [
        "healthy",
        "starting",
    ], f"Unexpected health status: {health_status}"

    # Check readiness
    is_ready = agent.is_ready()
    logger.info(f"Agent ready: {is_ready}")

    # Check liveness
    is_live = agent.is_live()
    assert is_live, "Agent should be live"

    logger.info("✅ Health checks passed")


async def test_task_execution(agent: SalesAgent):
    """Test basic task execution."""
    logger.info("🔍 Testing task execution...")

    task_description = (
        "Analyze the sales potential for a new SaaS product in the healthcare industry"
    )
    context = {
        "industry": "healthcare",
        "product_type": "SaaS",
        "target_market": "mid-market hospitals",
    }

    result = await agent.execute_task(task_description, context)

    assert result["status"] == "completed", f"Task failed: {result}"
    assert "result" in result, "Task result missing"
    assert result["agent_id"] == agent.config.agent_id, "Wrong agent ID in result"

    logger.info("✅ Task execution passed")


async def test_lead_qualification(agent: SalesAgent):
    """Test lead qualification functionality."""
    logger.info("🔍 Testing lead qualification...")

    # Create a test lead qualification message
    lead_data = {
        "lead_id": "test-lead-001",
        "company": "TechCorp Inc",
        "industry": "Technology",
        "size": "500 employees",
        "contact_name": "John Smith",
        "contact_title": "CTO",
        "budget": "$100k+",
        "timeline": "Q2 2024",
    }

    # Simulate task request message
    task_message = create_task_request(
        from_agent="test-requester",
        to_agent=agent.config.agent_id,
        task_description="Qualify this lead",
        context={"task_type": "lead_qualification", "lead_data": lead_data},
        priority=MessagePriority.HIGH,
    )

    # Handle the message
    response = await agent._handle_task_request(task_message)

    assert (
        response["status"] == "task_completed"
    ), f"Lead qualification failed: {response}"

    # Check sales metrics updated
    metrics = agent.get_sales_metrics()
    assert (
        metrics["sales_metrics"]["leads_qualified"] > 0
    ), "Lead qualification count not updated"

    logger.info("✅ Lead qualification passed")


async def test_cold_outreach(agent: SalesAgent):
    """Test cold outreach functionality."""
    logger.info("🔍 Testing cold outreach...")

    # Create test prospect data
    prospect_data = {
        "prospect_id": "test-prospect-001",
        "name": "Jane Doe",
        "company": "InnovateCorp",
        "title": "VP of Operations",
        "industry": "Manufacturing",
        "linkedin_url": "https://linkedin.com/in/janedoe",
    }

    # Simulate cold outreach task
    task_message = create_task_request(
        from_agent="test-requester",
        to_agent=agent.config.agent_id,
        task_description="Send cold outreach",
        context={
            "task_type": "cold_outreach",
            "prospect_data": prospect_data,
            "campaign_type": "email",
        },
    )

    # Handle the message
    response = await agent._handle_task_request(task_message)

    assert response["status"] == "task_completed", f"Cold outreach failed: {response}"

    # Check metrics updated
    metrics = agent.get_sales_metrics()
    assert metrics["sales_metrics"]["outreach_sent"] > 0, "Outreach count not updated"

    logger.info("✅ Cold outreach passed")


async def test_metrics(agent: SalesAgent):
    """Test agent metrics collection."""
    logger.info("🔍 Testing metrics collection...")

    # Get general metrics
    metrics = agent.get_metrics()
    required_fields = ["agent_id", "is_running", "tasks_completed", "health_status"]

    for field in required_fields:
        assert field in metrics, f"Missing metric field: {field}"

    # Get sales-specific metrics
    sales_metrics = agent.get_sales_metrics()
    sales_fields = ["leads_qualified", "outreach_sent", "conversion_rate"]

    for field in sales_fields:
        assert field in sales_metrics["sales_metrics"], f"Missing sales metric: {field}"

    logger.info(f"📊 Agent Metrics: {metrics}")
    logger.info(f"📈 Sales Metrics: {sales_metrics['sales_metrics']}")
    logger.info("✅ Metrics collection passed")


async def test_agent_discovery():
    """Test agent discovery functionality."""
    logger.info("🔍 Testing agent discovery...")

    # This would test the discovery service integration
    # For now, we'll just verify the agent card creation

    config = AgentConfig(
        agent_id="discovery-test-agent",
        role="Test Agent",
        goal="Test discovery",
        backstory="Test agent for discovery",
        department="test",
    )

    agent = SalesAgent(config)
    agent_card = agent.get_agent_card()

    assert agent_card.agent_id == config.agent_id
    assert "task_execution" in agent_card.capabilities
    assert "a2a_communication" in agent_card.capabilities
    assert agent_card.metadata["department"] == "test"

    logger.info("✅ Agent discovery passed")


if __name__ == "__main__":
    try:
        # Run the test
        asyncio.run(test_sales_agent())

        # Also test discovery
        asyncio.run(test_agent_discovery())

        logger.info("🎉 All distributed agent tests completed successfully!")

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)
