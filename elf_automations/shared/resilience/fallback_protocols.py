"""
Fallback protocols for graceful degradation

Implements various strategies for handling resource exhaustion:
1. Retry with backoff
2. Switch to alternative provider
3. Degrade service quality
4. Queue requests
5. Use cache
6. Circuit breaking
7. Load shedding
"""

import asyncio
import functools
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .circuit_breaker import CircuitBreaker
from .resource_manager import ResourceManager, ResourceStatus, ResourceType
from .retry_policies import ExponentialBackoff, RetryPolicy

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Available fallback strategies"""

    RETRY = "retry"
    SWITCH_PROVIDER = "switch_provider"
    DEGRADE_SERVICE = "degrade_service"
    QUEUE_REQUEST = "queue_request"
    USE_CACHE = "use_cache"
    CIRCUIT_BREAK = "circuit_break"
    LOAD_SHED = "load_shed"


class FallbackProtocol:
    """Manages fallback strategies for resource constraints"""

    def __init__(
        self,
        resource_manager: Optional[ResourceManager] = None,
        default_strategies: Optional[Dict[ResourceType, List[FallbackStrategy]]] = None,
    ):
        """
        Initialize fallback protocol manager

        Args:
            resource_manager: Resource manager instance
            default_strategies: Default fallback strategies per resource type
        """
        self.resource_manager = resource_manager or ResourceManager()

        # Default fallback chains
        self.default_strategies = default_strategies or {
            ResourceType.API_QUOTA: [
                FallbackStrategy.SWITCH_PROVIDER,
                FallbackStrategy.DEGRADE_SERVICE,
                FallbackStrategy.QUEUE_REQUEST,
            ],
            ResourceType.MEMORY: [
                FallbackStrategy.USE_CACHE,
                FallbackStrategy.DEGRADE_SERVICE,
                FallbackStrategy.LOAD_SHED,
            ],
            ResourceType.DATABASE: [
                FallbackStrategy.RETRY,
                FallbackStrategy.USE_CACHE,
                FallbackStrategy.CIRCUIT_BREAK,
            ],
            ResourceType.MCP_SERVER: [
                FallbackStrategy.RETRY,
                FallbackStrategy.CIRCUIT_BREAK,
                FallbackStrategy.USE_CACHE,
            ],
            ResourceType.NETWORK: [
                FallbackStrategy.RETRY,
                FallbackStrategy.CIRCUIT_BREAK,
            ],
        }

        # Circuit breakers per resource
        self._circuit_breakers = {}

        # Request queue
        self._request_queue = asyncio.Queue(maxsize=1000)

        # Cache for degraded responses
        self._degraded_cache = {}

    def get_circuit_breaker(self, resource_type: ResourceType) -> CircuitBreaker:
        """Get or create circuit breaker for resource"""
        if resource_type not in self._circuit_breakers:
            self._circuit_breakers[resource_type] = CircuitBreaker(
                failure_threshold=5, recovery_timeout=60, expected_exception=Exception
            )
        return self._circuit_breakers[resource_type]

    async def execute_with_fallback(
        self,
        func: Callable,
        resource_type: ResourceType,
        context: Optional[Dict[str, Any]] = None,
        strategies: Optional[List[FallbackStrategy]] = None,
        **kwargs,
    ) -> Any:
        """
        Execute function with fallback strategies

        Args:
            func: Function to execute
            resource_type: Resource type being used
            context: Execution context
            strategies: Override default strategies
            **kwargs: Arguments for func

        Returns:
            Function result or fallback result
        """
        # Check resource availability
        status, usage = self.resource_manager.check_resource(resource_type, context)

        if status == ResourceStatus.EXHAUSTED:
            logger.warning(
                f"Resource {resource_type.value} exhausted, applying fallback"
            )
            return await self._apply_fallback_chain(
                func, resource_type, context, strategies, **kwargs
            )

        # Try to execute normally
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)

            # Record successful usage
            self.resource_manager.record_usage(resource_type, 1, context)
            return result

        except Exception as e:
            logger.error(f"Error executing function: {e}")
            return await self._apply_fallback_chain(
                func, resource_type, context, strategies, error=e, **kwargs
            )

    async def _apply_fallback_chain(
        self,
        func: Callable,
        resource_type: ResourceType,
        context: Optional[Dict[str, Any]] = None,
        strategies: Optional[List[FallbackStrategy]] = None,
        error: Optional[Exception] = None,
        **kwargs,
    ) -> Any:
        """Apply fallback strategies in order"""

        strategies = strategies or self.default_strategies.get(resource_type, [])

        for strategy in strategies:
            try:
                logger.info(
                    f"Applying {strategy.value} strategy for {resource_type.value}"
                )

                if strategy == FallbackStrategy.RETRY:
                    return await self._retry_with_backoff(func, **kwargs)

                elif strategy == FallbackStrategy.SWITCH_PROVIDER:
                    return await self._switch_provider(
                        func, resource_type, context, **kwargs
                    )

                elif strategy == FallbackStrategy.DEGRADE_SERVICE:
                    return await self._degrade_service(
                        func, resource_type, context, **kwargs
                    )

                elif strategy == FallbackStrategy.QUEUE_REQUEST:
                    return await self._queue_request(
                        func, resource_type, context, **kwargs
                    )

                elif strategy == FallbackStrategy.USE_CACHE:
                    return await self._use_cache(func, resource_type, context, **kwargs)

                elif strategy == FallbackStrategy.CIRCUIT_BREAK:
                    cb = self.get_circuit_breaker(resource_type)
                    return await cb.call_async(func, **kwargs)

                elif strategy == FallbackStrategy.LOAD_SHED:
                    return self._load_shed(resource_type, context)

            except Exception as e:
                logger.warning(f"Fallback {strategy.value} failed: {e}")
                continue

        # All fallbacks failed
        raise Exception(f"All fallback strategies exhausted for {resource_type.value}")

    async def _retry_with_backoff(
        self, func: Callable, max_retries: int = 3, **kwargs
    ) -> Any:
        """Retry with exponential backoff"""
        policy = ExponentialBackoff(max_retries=max_retries)

        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(**kwargs)
                else:
                    return func(**kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = policy.get_delay(attempt)
                logger.info(
                    f"Retrying after {delay}s (attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)

    async def _switch_provider(
        self,
        func: Callable,
        resource_type: ResourceType,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """Switch to alternative provider"""

        # Get alternative resource
        alt_resource = self.resource_manager.get_alternative_resource(
            resource_type, context
        )

        if not alt_resource:
            raise Exception(f"No alternative provider for {resource_type.value}")

        # Update context with alternative
        new_context = (context or {}).copy()
        new_context.update(alt_resource)

        # Update kwargs if needed
        if "model" in alt_resource and "model" in kwargs:
            kwargs["model"] = alt_resource["model"]

        logger.info(f"Switching to alternative: {alt_resource}")

        # Try with alternative
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        else:
            return func(**kwargs)

    async def _degrade_service(
        self,
        func: Callable,
        resource_type: ResourceType,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """Provide degraded service"""

        # Check cache first
        cache_key = f"{func.__name__}:{str(kwargs)}"
        if cache_key in self._degraded_cache:
            cached_time, cached_result = self._degraded_cache[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=5):
                logger.info("Returning cached degraded response")
                return cached_result

        # Apply degradation based on resource type
        if resource_type == ResourceType.API_QUOTA:
            # Use simpler/cheaper model
            if "temperature" in kwargs:
                kwargs["temperature"] = 0  # More deterministic
            if "max_tokens" in kwargs:
                kwargs["max_tokens"] = min(kwargs["max_tokens"], 100)  # Limit response

        elif resource_type == ResourceType.MEMORY:
            # Reduce memory footprint
            if "batch_size" in kwargs:
                kwargs["batch_size"] = max(1, kwargs["batch_size"] // 2)

        # Execute with degraded parameters
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)

            # Cache degraded result
            self._degraded_cache[cache_key] = (datetime.now(), result)

            return result
        except Exception as e:
            logger.error(f"Degraded service also failed: {e}")
            raise

    async def _queue_request(
        self,
        func: Callable,
        resource_type: ResourceType,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """Queue request for later processing"""

        # Create request object
        request = {
            "func": func,
            "kwargs": kwargs,
            "resource_type": resource_type,
            "context": context,
            "timestamp": datetime.now(),
            "future": asyncio.Future(),
        }

        # Try to add to queue
        try:
            await self._request_queue.put(request)
            logger.info(f"Request queued (queue size: {self._request_queue.qsize()})")

            # Return future that will be resolved when processed
            return await request["future"]

        except asyncio.QueueFull:
            raise Exception("Request queue is full")

    async def _use_cache(
        self,
        func: Callable,
        resource_type: ResourceType,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """Use cached response if available"""

        # Simple cache key
        cache_key = f"{func.__name__}:{resource_type.value}:{str(kwargs)}"

        # Check if we have a cached response
        # In production, this would use Redis or similar
        logger.info("Cache miss - no cached response available")

        # Try to generate a minimal response
        if hasattr(func, "__name__") and "llm" in func.__name__.lower():
            return "I'm currently experiencing high load. Please try again later."

        raise Exception("No cached response available")

    def _load_shed(
        self, resource_type: ResourceType, context: Optional[Dict[str, Any]] = None
    ):
        """Shed load by rejecting request"""
        logger.warning(f"Load shedding activated for {resource_type.value}")
        raise Exception(
            f"System overloaded. Resource {resource_type.value} is at capacity. "
            "Please try again later."
        )

    async def process_queue(self):
        """Process queued requests when resources available"""
        while True:
            try:
                # Get request from queue
                request = await self._request_queue.get()

                # Check if resource is now available
                if self.resource_manager.can_use_resource(
                    request["resource_type"], request["context"]
                ):
                    # Process request
                    try:
                        func = request["func"]
                        kwargs = request["kwargs"]

                        if asyncio.iscoroutinefunction(func):
                            result = await func(**kwargs)
                        else:
                            result = func(**kwargs)

                        request["future"].set_result(result)

                    except Exception as e:
                        request["future"].set_exception(e)
                else:
                    # Re-queue if still not available
                    await self._request_queue.put(request)
                    await asyncio.sleep(5)  # Wait before retry

            except Exception as e:
                logger.error(f"Error processing queue: {e}")
                await asyncio.sleep(1)


# Decorator functions for easy use


def with_fallback(
    resource_type: ResourceType, strategies: Optional[List[FallbackStrategy]] = None
):
    """Decorator to add fallback protection to functions"""

    def decorator(func):
        # Get or create protocol instance
        protocol = FallbackProtocol()

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await protocol.execute_with_fallback(
                func, resource_type, strategies=strategies, *args, **kwargs
            )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Run async in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    protocol.execute_with_fallback(
                        func, resource_type, strategies=strategies, *args, **kwargs
                    )
                )
            finally:
                loop.close()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def with_retry(max_retries: int = 3, backoff: Optional[RetryPolicy] = None):
    """Decorator for simple retry logic"""

    policy = backoff or ExponentialBackoff(max_retries=max_retries)

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = policy.get_delay(attempt)
                    await asyncio.sleep(delay)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = policy.get_delay(attempt)
                    import time

                    time.sleep(delay)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def with_circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    """Decorator to add circuit breaker protection"""

    def decorator(func):
        cb = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=Exception,
        )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await cb.call_async(func, *args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
