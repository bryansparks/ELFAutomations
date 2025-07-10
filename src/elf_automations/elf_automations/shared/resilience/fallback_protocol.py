"""
Fallback Protocol System

Defines fallback strategies for different resource failures.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .resource_manager import ResourceState, ResourceStatus, ResourceType

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Types of fallback strategies"""

    RETRY = "retry"
    SWITCH_PROVIDER = "switch_provider"
    DEGRADE_SERVICE = "degrade_service"
    QUEUE_REQUEST = "queue_request"
    USE_CACHE = "use_cache"
    SCALE_DOWN = "scale_down"
    CIRCUIT_BREAK = "circuit_break"


@dataclass
class FallbackAction:
    """Action to take during fallback"""

    strategy: FallbackStrategy
    target: Optional[str] = None
    parameters: Dict[str, Any] = None
    priority: int = 0


class FallbackHandler(ABC):
    """Abstract base class for fallback handlers"""

    @abstractmethod
    async def handle(self, resource_state: ResourceState) -> bool:
        """Handle resource failure. Return True if handled successfully."""
        pass


class FallbackProtocol:
    """Manages fallback protocols for resource failures"""

    def __init__(self):
        self.protocols: Dict[ResourceType, List[FallbackAction]] = {}
        self.handlers: Dict[FallbackStrategy, FallbackHandler] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default fallback handlers"""
        self.handlers[FallbackStrategy.RETRY] = RetryHandler()
        self.handlers[FallbackStrategy.SWITCH_PROVIDER] = ProviderSwitchHandler()
        self.handlers[FallbackStrategy.DEGRADE_SERVICE] = DegradeServiceHandler()
        self.handlers[FallbackStrategy.QUEUE_REQUEST] = QueueRequestHandler()
        self.handlers[FallbackStrategy.USE_CACHE] = CacheHandler()
        self.handlers[FallbackStrategy.SCALE_DOWN] = ScaleDownHandler()
        self.handlers[FallbackStrategy.CIRCUIT_BREAK] = CircuitBreakHandler()

    def register_protocol(
        self, resource_type: ResourceType, actions: List[FallbackAction]
    ):
        """Register fallback protocol for a resource type"""
        # Sort by priority
        actions.sort(key=lambda x: x.priority)
        self.protocols[resource_type] = actions

    async def execute_fallback(self, resource_state: ResourceState) -> bool:
        """Execute fallback protocol for failed resource"""
        actions = self.protocols.get(resource_state.type, [])

        for action in actions:
            handler = self.handlers.get(action.strategy)
            if not handler:
                logger.warning(f"No handler for strategy {action.strategy}")
                continue

            try:
                # Set action parameters on handler
                if hasattr(handler, "set_parameters"):
                    handler.set_parameters(action)

                success = await handler.handle(resource_state)
                if success:
                    logger.info(
                        f"Fallback {action.strategy.value} succeeded for "
                        f"{resource_state.type.value}:{resource_state.name}"
                    )
                    return True

            except Exception as e:
                logger.error(f"Fallback handler failed: {e}")

        return False


class RetryHandler(FallbackHandler):
    """Handles retry logic with exponential backoff"""

    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0

    def set_parameters(self, action: FallbackAction):
        if action.parameters:
            self.max_retries = action.parameters.get("max_retries", 3)
            self.base_delay = action.parameters.get("base_delay", 1.0)

    async def handle(self, resource_state: ResourceState) -> bool:
        """Retry with exponential backoff"""
        for attempt in range(self.max_retries):
            delay = self.base_delay * (2**attempt)
            logger.info(
                f"Retrying after {delay}s (attempt {attempt + 1}/{self.max_retries})"
            )
            await asyncio.sleep(delay)

            # In real implementation, would retry the actual operation
            # For now, assume retry might succeed
            if attempt == self.max_retries - 1:
                return False

        return False


class ProviderSwitchHandler(FallbackHandler):
    """Switches to alternate provider"""

    def __init__(self):
        self.providers = {
            ResourceType.API_QUOTA: {
                "openai": ["anthropic", "cohere", "local"],
                "anthropic": ["openai", "cohere", "local"],
                "aws": ["gcp", "azure", "local"],
            },
            ResourceType.DATABASE: {
                "primary": ["replica1", "replica2", "cache"],
                "supabase": ["postgres", "sqlite", "memory"],
            },
            ResourceType.MCP_SERVER: {"primary": ["secondary", "tertiary", "mock"]},
        }
        self.target = None

    def set_parameters(self, action: FallbackAction):
        self.target = action.target

    async def handle(self, resource_state: ResourceState) -> bool:
        """Switch to alternate provider"""
        provider_map = self.providers.get(resource_state.type, {})
        current = resource_state.metadata.get("provider", resource_state.name)

        alternates = provider_map.get(current, [])
        if self.target and self.target in alternates:
            alternates = [self.target]

        for alternate in alternates:
            logger.info(f"Switching from {current} to {alternate}")
            # In real implementation, would switch provider
            # For now, assume switch succeeded
            return True

        return False


class DegradeServiceHandler(FallbackHandler):
    """Degrades service quality to reduce resource usage"""

    def __init__(self):
        self.degradation_levels = {
            ResourceType.API_QUOTA: [
                {"name": "reduce_model_quality", "savings": 0.7},
                {"name": "disable_embeddings", "savings": 0.5},
                {"name": "batch_requests", "savings": 0.3},
            ],
            ResourceType.MEMORY: [
                {"name": "clear_caches", "savings": 0.3},
                {"name": "reduce_batch_size", "savings": 0.2},
                {"name": "disable_features", "savings": 0.4},
            ],
            ResourceType.CPU: [
                {"name": "reduce_parallelism", "savings": 0.3},
                {"name": "increase_delays", "savings": 0.2},
                {"name": "disable_background_tasks", "savings": 0.3},
            ],
        }

    async def handle(self, resource_state: ResourceState) -> bool:
        """Apply service degradation"""
        degradations = self.degradation_levels.get(resource_state.type, [])

        for degradation in degradations:
            logger.info(f"Applying degradation: {degradation['name']}")
            # In real implementation, would apply degradation
            # For now, assume it helped
            if resource_state.usage_percent * (1 - degradation["savings"]) < 80:
                return True

        return False


class QueueRequestHandler(FallbackHandler):
    """Queues requests for later processing"""

    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.max_queue_size = 1000

    async def handle(self, resource_state: ResourceState) -> bool:
        """Queue request for later"""
        queue_name = f"{resource_state.type.value}:{resource_state.name}"

        if queue_name not in self.queues:
            self.queues[queue_name] = asyncio.Queue(maxsize=self.max_queue_size)

        queue = self.queues[queue_name]

        if queue.full():
            logger.warning(f"Queue {queue_name} is full")
            return False

        # In real implementation, would queue the actual request
        logger.info(f"Request queued in {queue_name} (size: {queue.qsize()})")
        return True


class CacheHandler(FallbackHandler):
    """Uses cached responses when resources unavailable"""

    def __init__(self):
        self.cache_store = {}
        self.cache_hit_rate = 0.0

    async def handle(self, resource_state: ResourceState) -> bool:
        """Try to use cached response"""
        cache_key = f"{resource_state.type.value}:{resource_state.name}"

        if cache_key in self.cache_store:
            logger.info(f"Using cached response for {cache_key}")
            # In real implementation, would return cached response
            return True

        logger.warning(f"No cache available for {cache_key}")
        return False


class ScaleDownHandler(FallbackHandler):
    """Scales down resource usage"""

    def __init__(self):
        self.scale_factors = {
            ResourceType.DOCKER: 0.5,
            ResourceType.K8S_POD: 0.5,
            ResourceType.MEMORY: 0.7,
            ResourceType.CPU: 0.7,
        }

    async def handle(self, resource_state: ResourceState) -> bool:
        """Scale down resource usage"""
        scale_factor = self.scale_factors.get(resource_state.type, 0.8)

        logger.info(
            f"Scaling down {resource_state.name} by {(1-scale_factor)*100:.0f}%"
        )

        # In real implementation, would scale down actual resources
        # For Docker/K8s, might reduce replicas
        # For memory/CPU, might reduce allocation

        new_usage = resource_state.usage_percent * scale_factor
        if new_usage < 80:
            return True

        return False


class CircuitBreakHandler(FallbackHandler):
    """Implements circuit breaker pattern"""

    def __init__(self):
        self.circuits: Dict[str, Dict[str, Any]] = {}
        self.failure_threshold = 5
        self.recovery_timeout = 60

    async def handle(self, resource_state: ResourceState) -> bool:
        """Open circuit breaker to prevent cascading failures"""
        circuit_name = f"{resource_state.type.value}:{resource_state.name}"

        if circuit_name not in self.circuits:
            self.circuits[circuit_name] = {
                "state": "closed",
                "failures": 0,
                "last_failure": None,
                "opened_at": None,
            }

        circuit = self.circuits[circuit_name]

        # Update failure count
        circuit["failures"] += 1
        circuit["last_failure"] = asyncio.get_event_loop().time()

        # Check if should open circuit
        if circuit["failures"] >= self.failure_threshold:
            circuit["state"] = "open"
            circuit["opened_at"] = asyncio.get_event_loop().time()
            logger.warning(f"Circuit breaker OPEN for {circuit_name}")

            # Schedule recovery check
            asyncio.create_task(self._schedule_recovery(circuit_name))
            return True

        return False

    async def _schedule_recovery(self, circuit_name: str):
        """Schedule circuit recovery check"""
        await asyncio.sleep(self.recovery_timeout)

        if circuit_name in self.circuits:
            circuit = self.circuits[circuit_name]
            circuit["state"] = "half_open"
            circuit["failures"] = 0
            logger.info(f"Circuit breaker HALF-OPEN for {circuit_name}")


# Default protocols for common scenarios
DEFAULT_PROTOCOLS = {
    ResourceType.API_QUOTA: [
        FallbackAction(FallbackStrategy.RETRY, parameters={"max_retries": 2}),
        FallbackAction(FallbackStrategy.SWITCH_PROVIDER, priority=1),
        FallbackAction(FallbackStrategy.DEGRADE_SERVICE, priority=2),
        FallbackAction(FallbackStrategy.QUEUE_REQUEST, priority=3),
    ],
    ResourceType.MEMORY: [
        FallbackAction(FallbackStrategy.USE_CACHE),
        FallbackAction(FallbackStrategy.DEGRADE_SERVICE, priority=1),
        FallbackAction(FallbackStrategy.SCALE_DOWN, priority=2),
    ],
    ResourceType.DATABASE: [
        FallbackAction(FallbackStrategy.RETRY, parameters={"max_retries": 3}),
        FallbackAction(FallbackStrategy.SWITCH_PROVIDER, target="replica", priority=1),
        FallbackAction(FallbackStrategy.USE_CACHE, priority=2),
        FallbackAction(FallbackStrategy.CIRCUIT_BREAK, priority=3),
    ],
    ResourceType.MCP_SERVER: [
        FallbackAction(FallbackStrategy.RETRY),
        FallbackAction(FallbackStrategy.SWITCH_PROVIDER, priority=1),
        FallbackAction(FallbackStrategy.CIRCUIT_BREAK, priority=2),
    ],
    ResourceType.DOCKER: [
        FallbackAction(FallbackStrategy.RETRY),
        FallbackAction(FallbackStrategy.SCALE_DOWN, priority=1),
    ],
    ResourceType.K8S_POD: [
        FallbackAction(FallbackStrategy.RETRY),
        FallbackAction(FallbackStrategy.SCALE_DOWN, priority=1),
        FallbackAction(FallbackStrategy.CIRCUIT_BREAK, priority=2),
    ],
}
