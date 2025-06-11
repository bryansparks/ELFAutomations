"""
Integration module for resilience components

Provides easy setup for teams to use fallback protocols.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .circuit_breaker import CircuitBreakerRegistry, circuit_breaker
from .fallback_protocol import DEFAULT_PROTOCOLS, FallbackProtocol
from .health_monitor import (
    HealthMonitor,
    check_cpu_health,
    check_disk_health,
    check_memory_health,
)
from .resource_manager import ResourceManager, ResourceStatus, ResourceType
from .retry_policy import RetryPolicies, retry

logger = logging.getLogger(__name__)


class ResilienceManager:
    """Main integration point for all resilience features"""

    def __init__(self, team_name: str, storage_path: Optional[Path] = None):
        """
        Initialize resilience manager for a team

        Args:
            team_name: Name of the team
            storage_path: Path for storing state
        """
        self.team_name = team_name
        self.storage_path = storage_path or Path(f"resilience/{team_name}")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.resource_manager = ResourceManager(
            storage_path=self.storage_path / "resources"
        )
        self.fallback_protocol = FallbackProtocol()
        self.circuit_registry = CircuitBreakerRegistry()
        self.health_monitor = HealthMonitor()

        # Setup default configurations
        self._setup_defaults()

    def _setup_defaults(self):
        """Setup default configurations"""
        # Register default fallback protocols
        for resource_type, actions in DEFAULT_PROTOCOLS.items():
            self.fallback_protocol.register_protocol(resource_type, actions)

        # Register default health checks
        self.health_monitor.register_health_check(
            "system", "memory", check_memory_health
        )
        self.health_monitor.register_health_check("system", "cpu", check_cpu_health)
        self.health_monitor.register_health_check("system", "disk", check_disk_health)

        # Register fallback handlers with resource manager
        for resource_type in ResourceType:
            self.resource_manager.register_fallback(
                resource_type,
                lambda state: self.fallback_protocol.execute_fallback(state),
            )

    async def start(self):
        """Start all monitoring services"""
        await self.resource_manager.start_monitoring()
        await self.health_monitor.start_monitoring()
        logger.info(f"Resilience manager started for team {self.team_name}")

    async def stop(self):
        """Stop all monitoring services"""
        await self.resource_manager.stop_monitoring()
        await self.health_monitor.stop_monitoring()
        logger.info(f"Resilience manager stopped for team {self.team_name}")

    # Convenience methods for teams

    def get_retry_policy(self, policy_type: str = "standard"):
        """Get pre-configured retry policy"""
        policies = {
            "quick": RetryPolicies.quick(),
            "standard": RetryPolicies.standard(),
            "aggressive": RetryPolicies.aggressive(),
            "network": RetryPolicies.network(),
            "database": RetryPolicies.database(),
        }
        return policies.get(policy_type, RetryPolicies.standard())

    def get_circuit_breaker(self, name: str, **kwargs):
        """Get or create circuit breaker"""
        return self.circuit_registry.get_or_create(f"{self.team_name}.{name}", **kwargs)

    async def with_resilience(
        self, func: Callable, resource_type: ResourceType, *args, **kwargs
    ) -> Any:
        """
        Execute function with full resilience stack

        Includes:
        - Circuit breaker
        - Retry policy
        - Resource monitoring
        - Fallback handling
        """
        # Get circuit breaker
        breaker = self.get_circuit_breaker(f"{resource_type.value}_operation")

        # Get retry policy
        retry_policy = self.get_retry_policy("standard")

        # Wrap function
        async def wrapped():
            # Check resource availability first
            resource_key = f"{resource_type.value}:{self.team_name}"
            if resource_key in self.resource_manager.resources:
                state = self.resource_manager.resources[resource_key]
                if state.status == ResourceStatus.FAILED:
                    logger.warning(
                        f"Resource {resource_key} is failed, triggering fallback"
                    )
                    await self.fallback_protocol.execute_fallback(state)

            # Execute with circuit breaker
            return await breaker.call(func, *args, **kwargs)

        # Execute with retry
        return await retry_policy.execute(wrapped)

    def register_api_quota_monitor(self, provider: str, check_func: Callable):
        """Register API quota monitoring"""
        self.resource_manager.register_monitor(
            ResourceType.API_QUOTA, f"{provider}_quota", check_func
        )

    def register_database_monitor(self, db_name: str, connection_func: Callable):
        """Register database monitoring"""
        self.resource_manager.register_monitor(
            ResourceType.DATABASE,
            db_name,
            lambda: self.resource_manager.check_database_connection(connection_func),
        )

    def register_mcp_monitor(
        self, server_name: str, gateway_url: str = "http://agentgateway.dev"
    ):
        """Register MCP server monitoring"""
        self.resource_manager.register_monitor(
            ResourceType.MCP_SERVER,
            server_name,
            lambda: self.resource_manager.check_mcp_server(server_name, gateway_url),
        )

    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        return {
            "team": self.team_name,
            "overall_health": self.health_monitor.get_overall_status().value,
            "components": {
                name: {
                    "status": health.status.value,
                    "uptime": health.uptime_seconds,
                    "error_rate": health.error_rate,
                    "last_check": health.last_check.isoformat(),
                }
                for name, health in self.health_monitor.health_status.items()
            },
            "resources": {
                name: {
                    "type": state.type.value,
                    "status": state.status.value,
                    "usage": state.usage_percent,
                    "last_check": state.last_check.isoformat(),
                }
                for name, state in self.resource_manager.resources.items()
            },
            "circuits": self.circuit_registry.get_all_stats(),
        }


# Decorators for easy usage


def with_fallback(resource_type: ResourceType):
    """Decorator to add fallback handling to async functions"""

    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            if hasattr(self, "resilience_manager"):
                return await self.resilience_manager.with_resilience(
                    func, resource_type, self, *args, **kwargs
                )
            else:
                # No resilience manager, just execute
                return await func(self, *args, **kwargs)

        return wrapper

    return decorator


# Example usage for teams
class ResilientTeamExample:
    """Example of how teams can use resilience features"""

    def __init__(self, team_name: str):
        self.team_name = team_name
        self.resilience_manager = ResilienceManager(team_name)

    async def start(self):
        """Start the team"""
        await self.resilience_manager.start()

        # Register custom monitors
        self.resilience_manager.register_mcp_monitor("supabase")
        self.resilience_manager.register_mcp_monitor("twilio")

    @with_fallback(ResourceType.API_QUOTA)
    async def call_llm(self, prompt: str):
        """Example LLM call with fallback"""
        # This would be actual LLM call
        pass

    @retry(max_attempts=3)
    @circuit_breaker("database_query")
    async def query_database(self, query: str):
        """Example database query with retry and circuit breaker"""
        # This would be actual database query
        pass

    async def get_status(self):
        """Get team resilience status"""
        return self.resilience_manager.get_health_report()
