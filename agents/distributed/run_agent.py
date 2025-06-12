#!/usr/bin/env python3
"""
Agent runner for distributed CrewAI + A2A agents.
Supports running different agent types based on environment configuration.
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

from base import AgentConfig
from examples.sales_agent import SalesAgent

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("agent_runner")


class AgentRunner:
    """Runner for distributed agents with graceful shutdown."""

    def __init__(self):
        self.agent: Optional[SalesAgent] = None
        self.shutdown_event = asyncio.Event()

    async def create_agent_from_env(self) -> SalesAgent:
        """Create agent from environment variables."""
        config = AgentConfig(
            agent_id=os.getenv("AGENT_ID", "default-agent"),
            role=os.getenv("AGENT_ROLE", "Default Agent"),
            goal=os.getenv("AGENT_GOAL", "Perform assigned tasks"),
            backstory=os.getenv("AGENT_BACKSTORY", "A helpful AI agent"),
            department=os.getenv("AGENT_DEPARTMENT", "general"),
            a2a_port=int(os.getenv("A2A_PORT", "8081")),
            health_port=int(os.getenv("HEALTH_PORT", "8080")),
            discovery_endpoint=os.getenv("DISCOVERY_ENDPOINT"),
            kubernetes_namespace=os.getenv("KUBERNETES_NAMESPACE", "default"),
            service_name=os.getenv("SERVICE_NAME", "agent-service"),
        )

        # For now, we only have SalesAgent implemented
        # In the future, this would route to different agent types
        agent_type = os.getenv("AGENT_TYPE", "sales")

        if agent_type == "sales":
            return SalesAgent(config)
        else:
            logger.warning(
                f"Unknown agent type '{agent_type}', defaulting to SalesAgent"
            )
            return SalesAgent(config)

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def run(self):
        """Run the agent with graceful shutdown."""
        try:
            # Setup signal handlers
            self.setup_signal_handlers()

            # Create and start agent
            self.agent = await self.create_agent_from_env()
            logger.info(f"Starting agent: {self.agent.config.agent_id}")

            await self.agent.start()

            # Wait for shutdown signal
            logger.info("Agent is running. Press Ctrl+C to stop.")
            await self.shutdown_event.wait()

        except Exception as e:
            logger.error(f"Agent failed: {e}")
            raise
        finally:
            if self.agent:
                logger.info("Stopping agent...")
                await self.agent.stop()
                logger.info("Agent stopped")


async def main():
    """Main entry point."""
    runner = AgentRunner()

    try:
        await runner.run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Agent runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
