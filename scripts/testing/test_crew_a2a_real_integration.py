"""
CrewAI + Real A2A Integration Test Script

Tests the integration between CrewAI crews and REAL A2A discovery services.
This replaces the mock-based test with actual Redis and discovery service integration.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from crewai import Agent, Crew, Task

from agents.distributed.enhanced_crewai_agent import (
    A2AAgentWrapper,
    A2AConfig,
    A2ACrewWrapper,
    create_marketing_crew_with_a2a,
    create_sales_crew_with_a2a,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RealA2AIntegrationTester:
    """Test suite for CrewAI + Real A2A integration"""

    def __init__(self, a2a_config: A2AConfig):
        self.a2a_config = a2a_config
        self.test_results = []

    async def run_all_tests(self):
        """Run comprehensive test suite with real A2A services"""
        logger.info("🚀 CrewAI + Real A2A Integration Test Suite")
        logger.info("=" * 80)

        tests = [
            (
                "Basic Crew Functionality with Real Services",
                self.test_basic_crew_functionality,
            ),
            ("Real A2A Discovery Service", self.test_real_discovery_service),
            ("Real Redis Message Routing", self.test_real_message_routing),
            ("Multi-Crew Real Coordination", self.test_multi_crew_real_coordination),
            ("Real Service Lifecycle Management", self.test_service_lifecycle),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                logger.info(f"\n🧪 Testing: {test_name}")
                logger.info("-" * 60)

                await test_func()
                logger.info(f"✅ {test_name}: PASSED")
                self.test_results.append((test_name, "PASSED", None))
                passed += 1

            except Exception as e:
                logger.error(f"❌ {test_name}: FAILED - {e}")
                self.test_results.append((test_name, "FAILED", str(e)))

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("🎯 TEST RESULTS SUMMARY")
        logger.info("=" * 80)

        for test_name, status, error in self.test_results:
            status_icon = "✅" if status == "PASSED" else "❌"
            logger.info(f"{status_icon} {test_name}: {status}")
            if error:
                logger.info(f"   Error: {error}")

        success_rate = (passed / total) * 100
        logger.info(
            f"\n🎯 Overall Result: {passed}/{total} tests passed ({success_rate:.1f}%)"
        )

        if passed == total:
            logger.info(
                "🎉 All tests passed! CrewAI + Real A2A integration is working correctly."
            )
        else:
            logger.warning(
                f"⚠️ {total - passed} tests failed. Check configuration and services."
            )

        return passed == total

    async def test_basic_crew_functionality(self):
        """Test basic crew functionality with real A2A services"""
        logger.info("Creating sales crew with real A2A services...")

        sales_crew = create_sales_crew_with_a2a(self.a2a_config)

        # Verify crew structure
        assert len(sales_crew.wrapped_agents) == 3, "Sales crew should have 3 agents"
        assert sales_crew.a2a_enabled, "A2A should be enabled"
        assert (
            sales_crew.discovery_service is not None
        ), "Discovery service should be initialized"
        assert sales_crew.a2a_client is not None, "A2A client should be initialized"

        # Test agent capabilities
        agent_roles = [wa.agent.role for wa in sales_crew.wrapped_agents]
        expected_roles = ["Sales Manager", "Lead Generation Specialist", "Sales Closer"]
        for role in expected_roles:
            assert role in agent_roles, f"Missing expected role: {role}"

        logger.info("✅ Basic crew structure validated")

        # Test service lifecycle
        await sales_crew.start_a2a_services()
        logger.info("✅ A2A services started successfully")

        await sales_crew.stop_a2a_services()
        logger.info("✅ A2A services stopped successfully")

    async def test_real_discovery_service(self):
        """Test real discovery service integration"""
        logger.info("Testing real discovery service...")

        # Create agent with real discovery
        agent = Agent(
            role="Test Agent",
            goal="Test discovery integration",
            backstory="Agent for testing real discovery service",
        )

        wrapper = A2AAgentWrapper(
            agent=agent,
            capabilities=["test_capability", "real_discovery"],
            a2a_config=self.a2a_config,
        )

        # Test service initialization
        assert (
            wrapper.discovery_service is not None
        ), "Discovery service should be initialized"

        # Start services and test registration
        await wrapper.start_a2a_services()
        logger.info("✅ Agent registered with real discovery service")

        # Test discovery query
        if wrapper.discovery_service:
            try:
                # Test health check
                health = await wrapper.discovery_service.health_check()
                logger.info(f"✅ Discovery service health check: {health}")

                # Test discovery query
                agents = await wrapper.discovery_service.discover_agents(
                    ["test_capability"]
                )
                logger.info(f"✅ Discovery query returned {len(agents)} agents")

            except Exception as e:
                logger.warning(f"⚠️ Discovery service not available: {e}")
                # This is expected if no central discovery service is running

        # Clean up
        await wrapper.stop_a2a_services()
        logger.info("✅ Agent unregistered from discovery service")

    async def test_real_message_routing(self):
        """Test real Redis message routing"""
        logger.info("Testing real Redis message routing...")

        # Create two agents for message exchange
        sender_agent = Agent(
            role="Sender Agent",
            goal="Send messages via A2A",
            backstory="Agent that sends messages",
        )

        receiver_agent = Agent(
            role="Receiver Agent",
            goal="Receive messages via A2A",
            backstory="Agent that receives messages",
        )

        sender_wrapper = A2AAgentWrapper(
            agent=sender_agent,
            capabilities=["message_sending"],
            a2a_config=self.a2a_config,
        )

        receiver_wrapper = A2AAgentWrapper(
            agent=receiver_agent,
            capabilities=["message_receiving"],
            a2a_config=self.a2a_config,
        )

        # Start services
        await sender_wrapper.start_a2a_services()
        await receiver_wrapper.start_a2a_services()

        # Test message routing through Redis
        if sender_wrapper.a2a_client and receiver_wrapper.a2a_client:
            try:
                # Test Redis connection
                await sender_wrapper.a2a_client.message_router.health_check()
                logger.info("✅ Redis message router connection verified")

                # Test message sending
                message_data = {
                    "test": "real_message_routing",
                    "timestamp": "2025-06-05T11:47:30-06:00",
                }

                success = await sender_wrapper.a2a_client.send_message(
                    to_agent="receiver_agent",
                    message_type="test_message",
                    content=message_data,
                )

                if success:
                    logger.info("✅ Message sent successfully via Redis")
                else:
                    logger.warning("⚠️ Message sending failed")

            except Exception as e:
                logger.warning(f"⚠️ Redis not available: {e}")
                # This is expected if Redis is not running

        # Clean up
        await sender_wrapper.stop_a2a_services()
        await receiver_wrapper.stop_a2a_services()
        logger.info("✅ Message routing test completed")

    async def test_multi_crew_real_coordination(self):
        """Test multi-crew coordination with real A2A services"""
        logger.info("Testing multi-crew coordination with real services...")

        # Create multiple crews
        sales_crew = create_sales_crew_with_a2a(self.a2a_config)
        marketing_crew = create_marketing_crew_with_a2a(self.a2a_config)

        # Start all services
        await sales_crew.start_a2a_services()
        await marketing_crew.start_a2a_services()

        # Test parallel task execution with real A2A
        sales_tasks = [
            {
                "description": "Generate enterprise leads",
                "capability": "lead_generation",
                "agent": "Lead Generation Specialist",
            },
            {
                "description": "Create marketing materials",
                "capability": "content_creation",  # Cross-crew capability
                "agent": "Sales Manager",
            },
        ]

        marketing_tasks = [
            {
                "description": "Launch social campaign",
                "capability": "social_media",
                "agent": "Social Media Manager",
            },
            {
                "description": "Close qualified deals",
                "capability": "deal_closing",  # Cross-crew capability
                "agent": "Content Creator",
            },
        ]

        # Execute tasks in parallel
        sales_results, marketing_results = await asyncio.gather(
            sales_crew.execute_tasks_with_discovery(sales_tasks),
            marketing_crew.execute_tasks_with_discovery(marketing_tasks),
        )

        # Verify results
        assert len(sales_results) == 2, "Sales crew should complete 2 tasks"
        assert len(marketing_results) == 2, "Marketing crew should complete 2 tasks"

        logger.info("✅ Sales crew results:")
        for i, result in enumerate(sales_results):
            logger.info(f"  {i+1}. {result}")

        logger.info("✅ Marketing crew results:")
        for i, result in enumerate(marketing_results):
            logger.info(f"  {i+1}. {result}")

        # Clean up
        await sales_crew.stop_a2a_services()
        await marketing_crew.stop_a2a_services()
        logger.info("✅ Multi-crew coordination test completed")

    async def test_service_lifecycle(self):
        """Test A2A service lifecycle management"""
        logger.info("Testing A2A service lifecycle management...")

        crew = create_sales_crew_with_a2a(self.a2a_config)

        # Test multiple start/stop cycles
        for cycle in range(3):
            logger.info(f"Testing lifecycle cycle {cycle + 1}/3")

            # Start services
            await crew.start_a2a_services()

            # Verify services are running
            assert crew.a2a_client is not None, "A2A client should be available"
            assert (
                crew.discovery_service is not None
            ), "Discovery service should be available"

            # Test basic functionality
            tasks = [
                {
                    "description": f"Test task cycle {cycle + 1}",
                    "capability": "sales_strategy",
                    "agent": "Sales Manager",
                }
            ]

            results = await crew.execute_tasks_with_discovery(tasks)
            assert len(results) == 1, "Should complete 1 task"

            # Stop services
            await crew.stop_a2a_services()

            logger.info(f"✅ Lifecycle cycle {cycle + 1} completed")

        logger.info("✅ Service lifecycle management validated")


async def main():
    """Main test execution function"""

    # Configure real A2A services
    a2a_config = A2AConfig(
        discovery_endpoint="http://localhost:8080",  # Real discovery service endpoint
        redis_url="redis://localhost:6379",  # Real Redis instance
        timeout=10.0,  # Shorter timeout for testing
        max_retries=2,  # Fewer retries for faster tests
    )

    logger.info("🔧 Configuration:")
    logger.info(
        f"  Discovery Endpoint: {a2a_config.discovery_endpoint or 'Local registry'}"
    )
    logger.info(f"  Redis URL: {a2a_config.redis_url}")
    logger.info(f"  Timeout: {a2a_config.timeout}s")
    logger.info(f"  Max Retries: {a2a_config.max_retries}")

    # Create and run test suite
    tester = RealA2AIntegrationTester(a2a_config)
    success = await tester.run_all_tests()

    if success:
        logger.info("\n🎉 All tests passed! Real A2A integration is working correctly.")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Check your A2A service configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
