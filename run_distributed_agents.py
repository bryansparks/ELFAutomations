"""
Distributed agents runner with A2A communication.
This script runs multiple agents with proper A2A communication between them.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, "/app")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from agents.distributed.a2a.messages import MessageType, create_message

# Import distributed agent components - REQUIRED, no fallback
from agents.distributed.base.distributed_agent import (
    AgentConfig,
    DistributedCrewAIAgent,
)

logger.info("✅ Distributed agent components imported successfully")

import threading

# Health check endpoints
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agent_id": os.getenv("AGENT_ID", "distributed-agents"),
                "role": os.getenv("AGENT_ROLE", "Multi-Agent System"),
            }
            self.wfile.write(json.dumps(response).encode())

        elif self.path == "/ready":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"status": "ready", "timestamp": datetime.now().isoformat()}
            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default HTTP server logs
        pass


def start_health_server():
    """Start the health check server."""
    server = HTTPServer(("0.0.0.0", 8091), HealthCheckHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    logger.info("🏥 Health check server started on port 8091")
    return server


async def create_distributed_agents():
    """Create multiple distributed agents for testing A2A communication."""
    agents = []

    # Chief AI Agent
    chief_config = AgentConfig(
        agent_id="chief-ai-agent",
        role="Chief Executive Officer",
        goal="Provide strategic leadership and coordinate all departments for optimal business performance",
        backstory="You are the Chief AI Agent, responsible for strategic planning, performance monitoring, and cross-departmental coordination. You have extensive experience in executive leadership and business strategy.",
        department="Executive",
        a2a_host="0.0.0.0",
        a2a_port=8090,
        discovery_endpoint=os.getenv(
            "DISCOVERY_ENDPOINT", "http://discovery-service:8080"
        ),
    )

    # Sales Agent
    sales_config = AgentConfig(
        agent_id="sales-agent",
        role="Sales Director",
        goal="Drive revenue growth through effective sales strategies and customer relationship management",
        backstory="You are a seasoned sales professional with expertise in B2B sales, customer acquisition, and revenue optimization. You work closely with marketing and customer success teams.",
        department="Sales",
        a2a_host="0.0.0.0",
        a2a_port=8092,
        discovery_endpoint=os.getenv(
            "DISCOVERY_ENDPOINT", "http://discovery-service:8080"
        ),
    )

    # Marketing Agent
    marketing_config = AgentConfig(
        agent_id="marketing-agent",
        role="Marketing Director",
        goal="Create compelling marketing campaigns and generate high-quality leads for the sales team",
        backstory="You are a creative marketing expert with deep knowledge of digital marketing, content strategy, and lead generation. You collaborate closely with sales and product teams.",
        department="Marketing",
        a2a_host="0.0.0.0",
        a2a_port=8093,
        discovery_endpoint=os.getenv(
            "DISCOVERY_ENDPOINT", "http://discovery-service:8080"
        ),
    )

    # Create agents
    try:
        chief_agent = DistributedCrewAIAgent(chief_config)
        sales_agent = DistributedCrewAIAgent(sales_config)
        marketing_agent = DistributedCrewAIAgent(marketing_config)

        agents = [chief_agent, sales_agent, marketing_agent]
        logger.info(f"✅ Created {len(agents)} distributed agents")

    except Exception as e:
        logger.error(f"❌ Failed to create distributed agents: {e}")
        raise

    return agents


async def test_a2a_communication(agents):
    """Test A2A communication between agents."""
    chief_agent = agents[0]  # Chief AI Agent
    sales_agent = agents[1]  # Sales Agent

    try:
        # Create a message from Chief to Sales
        message = create_message(
            message_type=MessageType.TASK_REQUEST,
            from_agent=chief_agent.config.agent_id,
            to_agent=sales_agent.config.agent_id,
            content={
                "task_description": "Generate Q1 sales strategy",
                "task": "Generate Q1 sales strategy",
                "priority": "high",
                "deadline": "2024-01-31",
                "context": "We need to increase revenue by 25% this quarter",
            },
        )

        # Send message via A2A
        if (
            hasattr(chief_agent, "a2a_client_manager")
            and chief_agent.a2a_client_manager
        ):
            result = await chief_agent.a2a_client_manager.send_message(
                sales_agent.config.agent_id, message
            )
            logger.info(f"✅ A2A message sent: {result}")
        else:
            logger.warning("⚠️ A2A client manager not available")

    except Exception as e:
        logger.error(f"❌ A2A communication test failed: {e}")


async def run_distributed_system():
    """Run the distributed agent system with A2A communication."""
    logger.info("🚀 Starting distributed agent system...")

    # Start health server
    health_server = start_health_server()

    try:
        # Create distributed agents
        agents = await create_distributed_agents()

        # Start all agents
        for agent in agents:
            await agent.start()
            logger.info(f"✅ Started agent: {agent.config.agent_id}")

        # Test A2A communication
        await test_a2a_communication(agents)

        # Main operation loop
        cycle_count = 0
        while True:
            cycle_count += 1
            logger.info(f"🔄 Starting operation cycle #{cycle_count}")

            try:
                # Coordinate agents for business tasks
                await coordinate_business_operations(agents)

                logger.info(f"✅ Operation cycle #{cycle_count} completed")

            except Exception as e:
                logger.error(f"❌ Error in operation cycle #{cycle_count}: {e}")

            # Wait before next cycle (30 minutes)
            await asyncio.sleep(1800)

    except Exception as e:
        logger.error(f"❌ Failed to run distributed system: {e}")
        raise
    finally:
        # Cleanup
        if "agents" in locals():
            for agent in agents:
                try:
                    await agent.stop()
                except Exception as e:
                    logger.error(f"Error stopping agent {agent.config.agent_id}: {e}")


async def coordinate_business_operations(agents):
    """Coordinate business operations across multiple agents."""
    chief_agent = next((a for a in agents if "chief" in a.config.agent_id), None)
    sales_agent = next((a for a in agents if "sales" in a.config.agent_id), None)
    marketing_agent = next(
        (a for a in agents if "marketing" in a.config.agent_id), None
    )

    if not all([chief_agent, sales_agent, marketing_agent]):
        logger.warning("Not all required agents available for coordination")
        return

    # Chief agent creates strategic tasks
    strategic_task = {
        "type": "strategic_planning",
        "content": "Analyze current market conditions and create quarterly business strategy",
        "requires_input_from": ["sales", "marketing"],
    }

    # Sales agent creates sales tasks
    sales_task = {
        "type": "sales_analysis",
        "content": "Analyze sales pipeline and forecast Q1 revenue",
        "reports_to": "chief",
    }

    # Marketing agent creates marketing tasks
    marketing_task = {
        "type": "marketing_campaign",
        "content": "Design lead generation campaign for Q1 targets",
        "coordinates_with": "sales",
    }

    # Execute tasks with CrewAI
    tasks = []

    # Create CrewAI tasks for each agent
    from crewai import Crew, Task

    chief_task = Task(
        description=strategic_task["content"],
        agent=chief_agent.crew_agent,
        expected_output="Strategic business plan with quarterly objectives and resource allocation",
    )

    sales_task_crew = Task(
        description=sales_task["content"],
        agent=sales_agent.crew_agent,
        expected_output="Sales forecast and pipeline analysis with revenue projections",
    )

    marketing_task_crew = Task(
        description=marketing_task["content"],
        agent=marketing_agent.crew_agent,
        expected_output="Marketing campaign strategy with lead generation targets",
    )

    # Create crew with all agents
    crew = Crew(
        agents=[
            chief_agent.crew_agent,
            sales_agent.crew_agent,
            marketing_agent.crew_agent,
        ],
        tasks=[chief_task, sales_task_crew, marketing_task_crew],
        verbose=True,
    )

    # Execute the crew
    result = crew.kickoff()
    logger.info(f"📊 Crew execution result: {str(result)[:200]}...")


if __name__ == "__main__":
    logger.info("🎯 Starting distributed agents with A2A communication...")

    try:
        asyncio.run(run_distributed_system())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down distributed agent system...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
