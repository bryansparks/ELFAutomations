#!/usr/bin/env python3
"""
ELF Automations Demo Script

This script demonstrates the Virtual AI Company Platform capabilities.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import structlog
from dotenv import load_dotenv

from agents.executive.chief_ai_agent import ChiefAIAgent
from agents.registry import AgentRegistry
from mcp_servers.business_tools import BusinessToolsServer

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def demo_basic_agent_functionality():
    """Demonstrate basic agent functionality."""
    logger.info("=== Demo: Basic Agent Functionality ===")

    # Create and start Chief AI Agent
    chief = ChiefAIAgent()
    await chief.start()

    logger.info("Chief AI Agent started", agent_id=chief.agent_id)

    # Show agent status
    status = chief.get_status()
    logger.info("Chief AI Agent status", status=status)

    # Check if we have API keys for real LLM calls
    has_anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))

    if has_anthropic_key:
        logger.info(" Running with real LLM integration")

        # Test simple thinking task
        logger.info("Testing LLM thinking capability")
        try:
            thought = await chief.think(
                "What are the key priorities for a Chief AI Agent in a virtual company?"
            )
            logger.info(
                "Chief AI thought",
                thought=thought[:200] + "..." if len(thought) > 200 else thought,
            )
        except Exception as e:
            logger.error("LLM thinking failed", error=str(e))

        # Test strategic planning with real LLM
        planning_task = {
            "type": "strategic_planning",
            "context": {
                "time_horizon": "quarterly",
                "focus_areas": [
                    "AI agent efficiency",
                    "scalability",
                    "cost optimization",
                ],
                "current_metrics": {
                    "active_agents": 1,
                    "task_completion_rate": 0.95,
                    "avg_response_time": "2.3s",
                },
            },
        }

        logger.info("Executing strategic planning with real LLM")
        try:
            result = await chief.execute_task(planning_task)
            logger.info(
                "Strategic planning completed",
                result_type=type(result).__name__,
                result_preview=str(result)[:300] + "..."
                if len(str(result)) > 300
                else str(result),
            )
        except Exception as e:
            logger.error("Strategic planning failed", error=str(e))

    else:
        logger.info(" Running in mock mode (no API keys)")

        # Test strategic planning task (will use mock responses)
        planning_task = {
            "type": "strategic_planning",
            "context": {
                "time_horizon": "quarterly",
                "focus_areas": ["growth", "efficiency", "innovation"],
            },
        }

        logger.info("Executing strategic planning task (mock mode)")
        try:
            result = await chief.execute_task(planning_task)
            logger.info("Strategic planning completed (mock)", result=result)
        except Exception as e:
            logger.error("Strategic planning failed", error=str(e))

    # Show registry stats
    stats = AgentRegistry.get_registry_stats()
    logger.info("Agent Registry stats", stats=stats)

    # Stop the agent
    await chief.stop()
    logger.info("Chief AI Agent stopped")


async def demo_mcp_server_functionality():
    """Demonstrate MCP server functionality."""
    logger.info("=== Demo: MCP Server Functionality ===")

    # Create Business Tools MCP Server (without database for demo)
    business_server = BusinessToolsServer()
    await business_server.start()

    logger.info("Business Tools MCP Server started")

    # List available tools
    tools = business_server.get_tools()
    logger.info("Available MCP tools", count=len(tools))

    for tool in tools[:5]:  # Show first 5 tools
        logger.info("Tool available", name=tool.name, description=tool.description)

    # List available resources
    resources = business_server.get_resources()
    logger.info("Available MCP resources", count=len(resources))

    for resource in resources:
        logger.info(
            "Resource available",
            uri=resource.uri,
            name=resource.name,
            description=resource.description,
        )

    # Test reading a resource
    try:
        customers_resource = await business_server.read_resource("business://customers")
        logger.info("Read customers resource", content=customers_resource)
    except Exception as e:
        logger.error("Failed to read resource", error=str(e))

    # Stop the server
    await business_server.stop()
    logger.info("Business Tools MCP Server stopped")


async def demo_agent_communication():
    """Demonstrate agent communication."""
    logger.info("=== Demo: Agent Communication ===")

    # Create Chief AI Agent
    chief = ChiefAIAgent()
    await chief.start()

    # Simulate sending a message to a department head
    message_id = await chief.send_message(
        to_agent="sales-head-001",
        message_type="quarterly_review_request",
        content={
            "quarter": "Q4 2024",
            "metrics_required": ["revenue", "pipeline", "conversion_rate"],
            "deadline": "2024-12-31",
        },
    )

    logger.info("Message sent", message_id=message_id)

    # Process any incoming messages
    await chief.process_messages()

    # Show message queue status
    status = chief.get_status()
    logger.info(
        "Chief status after messaging", message_queue_size=status["message_queue_size"]
    )

    await chief.stop()


async def demo_error_handling():
    """Demonstrate error handling and resilience."""
    logger.info("=== Demo: Error Handling ===")

    chief = ChiefAIAgent()
    await chief.start()

    # Test with an invalid task type
    invalid_task = {"type": "invalid_task_type", "context": {"test": "data"}}

    logger.info("Testing error handling with invalid task")
    try:
        result = await chief.execute_task(invalid_task)
        logger.info("Unexpected success", result=result)
    except Exception as e:
        logger.info("Expected error caught", error=str(e))

    # Check error count in state
    status = chief.get_status()
    logger.info(
        "Agent status after error",
        error_count=status["error_count"],
        status=status["status"],
    )

    await chief.stop()


async def main():
    """Main demo function."""
    logger.info("Starting ELF Automations Demo")

    # Load environment variables
    load_dotenv()

    # Check if we have required API keys for full demo
    has_anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))

    if not has_anthropic_key:
        logger.warning("ANTHROPIC_API_KEY not found - some demos may be limited")

    try:
        # Run basic functionality demo
        await demo_basic_agent_functionality()

        # Run MCP server demo
        await demo_mcp_server_functionality()

        # Run communication demo
        await demo_agent_communication()

        # Run error handling demo
        await demo_error_handling()

        logger.info("Demo completed successfully!")

    except Exception as e:
        logger.error("Demo failed", error=str(e))
        return 1

    finally:
        # Cleanup
        await AgentRegistry.shutdown_all_agents()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
