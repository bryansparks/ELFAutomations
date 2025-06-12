#!/usr/bin/env python3
"""
Run Chief AI Agent Script

This script starts and runs the Chief AI Agent for the Virtual AI Company Platform.
"""

import asyncio
import os
import signal
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import structlog
from dotenv import load_dotenv

from agents.executive.chief_ai_agent import ChiefAIAgent
from agents.registry import AgentRegistry

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
        structlog.dev.ConsoleRenderer(),  # Human-readable console output
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class ChiefAIRunner:
    """Runner for the Chief AI Agent."""

    def __init__(self):
        self.chief_agent: ChiefAIAgent = None
        self.running = False

    async def start(self):
        """Start the Chief AI Agent."""
        logger.info("Starting Chief AI Agent runner")

        try:
            # Initialize and start the Chief AI Agent
            self.chief_agent = ChiefAIAgent()
            await self.chief_agent.start()

            logger.info(
                "Chief AI Agent started successfully",
                agent_id=self.chief_agent.agent_id,
            )

            # Start performance monitoring
            monitoring_task = asyncio.create_task(
                self.chief_agent.start_performance_monitoring()
            )

            # Start message processing loop
            message_task = asyncio.create_task(self._message_processing_loop())

            self.running = True

            # Wait for shutdown signal
            await self._wait_for_shutdown()

            # Cancel background tasks
            monitoring_task.cancel()
            message_task.cancel()

            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass

            try:
                await message_task
            except asyncio.CancelledError:
                pass

        except Exception as e:
            logger.error("Error starting Chief AI Agent", error=str(e))
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the Chief AI Agent."""
        logger.info("Stopping Chief AI Agent runner")

        self.running = False

        if self.chief_agent:
            await self.chief_agent.stop()
            logger.info("Chief AI Agent stopped")

        # Shutdown all agents in registry
        await AgentRegistry.shutdown_all_agents()
        logger.info("All agents shut down")

    async def _message_processing_loop(self):
        """Background message processing loop."""
        while self.running:
            try:
                if self.chief_agent:
                    await self.chief_agent.process_messages()
                await asyncio.sleep(1)  # Process messages every second
            except Exception as e:
                logger.error("Error in message processing loop", error=str(e))
                await asyncio.sleep(5)  # Wait longer on error

    async def _wait_for_shutdown(self):
        """Wait for shutdown signal."""
        shutdown_event = asyncio.Event()

        def signal_handler():
            logger.info("Received shutdown signal")
            shutdown_event.set()

        # Set up signal handlers
        if sys.platform != "win32":
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, signal_handler)

        # Wait for shutdown signal
        await shutdown_event.wait()


async def main():
    """Main function."""
    # Load environment variables
    load_dotenv()

    # Check for required environment variables
    required_env_vars = ["ANTHROPIC_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error("Missing required environment variables", missing=missing_vars)
        sys.exit(1)

    # Create and run the Chief AI Agent
    runner = ChiefAIRunner()

    try:
        await runner.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        sys.exit(1)

    logger.info("Chief AI Agent runner finished")


if __name__ == "__main__":
    asyncio.run(main())
