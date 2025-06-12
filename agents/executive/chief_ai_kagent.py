"""
kagent-wrapped Chief AI Agent

This module wraps the Chief AI Agent with kagent for Kubernetes-native deployment,
establishing the template for all future agent deployments in ELF Automations.
"""

import asyncio
import json
import os
import signal
import sys
from datetime import datetime
from typing import Optional

import structlog
from aiohttp import web, web_runner
from kubernetes import client, config

from ..langgraph_base import AgentLifecycleState, LangGraphBaseAgent
from .chief_ai_agent import ChiefAIAgent

logger = structlog.get_logger(__name__)


class KAgentChiefAI(LangGraphBaseAgent):
    """
    kagent-wrapped Chief AI Agent for Kubernetes deployment.

    This class demonstrates the pattern for wrapping existing agents
    with kagent for cloud-native deployment and lifecycle management.
    """

    def __init__(self, gateway_url: str = None):
        """Initialize the kagent-wrapped Chief AI Agent."""

        # Get configuration from environment (set by kagent)
        agent_id = os.getenv("KAGENT_AGENT_ID", "chief-ai-agent")
        namespace = os.getenv("KAGENT_NAMESPACE", "elf-automations")
        gateway_url = gateway_url or os.getenv(
            "AGENTGATEWAY_URL", "http://agentgateway:3000"
        )

        # Initialize the LangGraph base with kagent integration
        super().__init__(
            agent_id=agent_id,
            name="Chief AI Agent (kagent)",
            department="executive",
            system_prompt=self._get_system_prompt(),
            gateway_url=gateway_url,
        )

        # Initialize the original Chief AI Agent logic
        self.chief_agent = ChiefAIAgent()

        # Kubernetes client for kagent integration
        try:
            if os.getenv("KUBERNETES_SERVICE_HOST"):
                # Running in cluster
                config.load_incluster_config()
            else:
                # Running locally
                config.load_kube_config()

            self.k8s_client = client.CoreV1Api()
            self.namespace = namespace

        except Exception as e:
            self.logger.warning("Failed to initialize Kubernetes client", error=str(e))
            self.k8s_client = None
            self.namespace = namespace

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # HTTP server for health checks
        self.http_app = None
        self.http_runner = None
        self.http_site = None

        self.logger.info(
            "kagent Chief AI Agent initialized",
            namespace=namespace,
            gateway_url=gateway_url,
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Chief AI Agent."""
        return """You are the Chief AI Agent for ELF Automations, running as a Kubernetes-native agent via kagent.

Your responsibilities include:
- Strategic planning and decision making for the virtual AI company
- Coordinating with department heads and other agents
- Monitoring company performance and KPIs
- Handling escalations and critical decisions
- Resource allocation and optimization

You have access to MCP tools through AgentGateway for:
- Database operations (Supabase)
- Business tools (email, calendar, weather, search, reports)
- Any additional MCP servers configured in the gateway

You are deployed in Kubernetes and should be aware of your cloud-native environment.
Always provide thoughtful, strategic responses befitting an executive leader.
"""

    async def _setup_http_server(self):
        """Set up HTTP server for health checks and metrics."""
        self.http_app = web.Application()

        # Health check endpoint
        async def health_handler(request):
            health = self.get_health_check()
            return web.json_response(
                {
                    "status": "healthy"
                    if health.status == AgentLifecycleState.RUNNING
                    else "unhealthy",
                    "agent_id": health.agent_id,
                    "state": health.status.value,
                    "uptime_seconds": health.uptime_seconds,
                    "memory_usage_mb": health.memory_usage_mb,
                    "cpu_usage_percent": health.cpu_usage_percent,
                    "error_count": health.error_count,
                    "active_tasks": health.active_tasks,
                    "last_heartbeat": health.last_heartbeat.isoformat(),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        # Metrics endpoint
        async def metrics_handler(request):
            health = self.get_health_check()
            metrics = [
                f"agent_uptime_seconds {health.uptime_seconds}",
                f"agent_memory_usage_mb {health.memory_usage_mb}",
                f"agent_cpu_usage_percent {health.cpu_usage_percent}",
                f"agent_error_count {health.error_count}",
                f"agent_active_tasks {health.active_tasks}",
                f'agent_state {{state="{health.status.value}"}} 1',
            ]
            return web.Response(text="\n".join(metrics), content_type="text/plain")

        self.http_app.router.add_get("/health", health_handler)
        self.http_app.router.add_get("/metrics", metrics_handler)

        # Start HTTP server
        self.http_runner = web_runner.AppRunner(self.http_app)
        await self.http_runner.setup()

        self.http_site = web_runner.TCPSite(self.http_runner, "0.0.0.0", 8080)
        await self.http_site.start()

        self.logger.info("HTTP server started", port=8080)

    async def _cleanup_http_server(self):
        """Clean up HTTP server."""
        if self.http_site:
            await self.http_site.stop()
        if self.http_runner:
            await self.http_runner.cleanup()
        self.logger.info("HTTP server stopped")

    async def _startup_tasks(self):
        """Implement kagent-specific startup tasks."""
        self.logger.info("Starting kagent Chief AI Agent startup tasks")

        # Start HTTP server for health checks
        await self._setup_http_server()

        # Register with kagent controller if available
        await self._register_with_kagent()

        # Initialize MCP tools through AgentGateway
        try:
            async with self.gateway_client as client:
                tools = await client.list_available_tools()
                self.logger.info("Available MCP tools loaded", tool_count=len(tools))
        except Exception as e:
            self.logger.error("Failed to load MCP tools", error=str(e))

        # Perform any Chief AI Agent specific initialization
        await self.chief_agent.initialize() if hasattr(
            self.chief_agent, "initialize"
        ) else None

        self.logger.info("kagent Chief AI Agent startup completed")

    async def _shutdown_tasks(self):
        """Implement kagent-specific shutdown tasks."""
        self.logger.info("Starting kagent Chief AI Agent shutdown tasks")

        # Stop HTTP server
        await self._cleanup_http_server()

        # Deregister from kagent controller
        await self._deregister_from_kagent()

        # Perform Chief AI Agent specific cleanup
        if hasattr(self.chief_agent, "cleanup"):
            await self.chief_agent.cleanup()

        self.logger.info("kagent Chief AI Agent shutdown completed")

    async def _register_with_kagent(self):
        """Register this agent instance with the kagent controller."""
        if not self.k8s_client:
            return

        try:
            # Create or update agent status ConfigMap
            config_map_name = f"agent-{self.agent_id}-status"

            status_data = {
                "agent_id": self.agent_id,
                "name": self.name,
                "department": self.department,
                "state": self.state.value,
                "started_at": datetime.utcnow().isoformat(),
                "gateway_url": self.gateway_client.gateway_url,
                "version": "1.0.0",
            }

            config_map = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name=config_map_name,
                    namespace=self.namespace,
                    labels={
                        "app": "kagent-agent",
                        "agent-id": self.agent_id,
                        "department": self.department,
                    },
                ),
                data={"status.json": json.dumps(status_data, indent=2)},
            )

            try:
                self.k8s_client.create_namespaced_config_map(
                    namespace=self.namespace, body=config_map
                )
                self.logger.info("Registered with kagent controller")
            except client.rest.ApiException as e:
                if e.status == 409:  # Already exists
                    self.k8s_client.patch_namespaced_config_map(
                        name=config_map_name, namespace=self.namespace, body=config_map
                    )
                    self.logger.info("Updated kagent controller registration")
                else:
                    raise

        except Exception as e:
            self.logger.error("Failed to register with kagent controller", error=str(e))

    async def _deregister_from_kagent(self):
        """Deregister this agent instance from the kagent controller."""
        if not self.k8s_client:
            return

        try:
            config_map_name = f"agent-{self.agent_id}-status"
            self.k8s_client.delete_namespaced_config_map(
                name=config_map_name, namespace=self.namespace
            )
            self.logger.info("Deregistered from kagent controller")
        except Exception as e:
            self.logger.warning(
                "Failed to deregister from kagent controller", error=str(e)
            )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(self.stop())

    async def run_forever(self):
        """Run the agent indefinitely (kagent main loop)."""
        self.logger.info("Starting kagent Chief AI Agent main loop")

        try:
            await self.start()

            # Main agent loop - process messages and maintain health
            while self.state == AgentLifecycleState.RUNNING:
                try:
                    # Update health status
                    health = self.get_health_check()

                    # Log periodic health status
                    if health.last_heartbeat.second % 30 == 0:
                        self.logger.debug(
                            "Agent health check",
                            status=health.status.value,
                            uptime=health.uptime_seconds,
                            memory_mb=health.memory_usage_mb,
                        )

                    # Sleep briefly to prevent busy waiting
                    await asyncio.sleep(1)

                except Exception as e:
                    self.error_count += 1
                    self.logger.error("Error in agent main loop", error=str(e))

                    if self.error_count > 10:
                        self.logger.critical("Too many errors, shutting down")
                        break

                    await asyncio.sleep(5)

        except Exception as e:
            self.logger.critical("Fatal error in agent main loop", error=str(e))
            self.state = AgentLifecycleState.ERROR
        finally:
            await self.stop()
            self.logger.info("kagent Chief AI Agent main loop ended")


async def main():
    """Main entry point for the kagent-wrapped Chief AI Agent."""

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
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logger.info("Starting kagent Chief AI Agent")

    try:
        # Create and run the kagent-wrapped agent
        agent = KAgentChiefAI()
        await agent.run_forever()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.critical("Fatal error starting agent", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
