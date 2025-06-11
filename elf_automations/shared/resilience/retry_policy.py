"""
Retry Policy Implementation

Provides configurable retry strategies with backoff.
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, List, Optional, Type, Union

logger = logging.getLogger(__name__)


class RetryStrategy(ABC):
    """Abstract base class for retry strategies"""

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay in seconds for given attempt"""
        pass


class FixedDelay(RetryStrategy):
    """Fixed delay between retries"""

    def __init__(self, delay: float):
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        return self.delay


class ExponentialBackoff(RetryStrategy):
    """Exponential backoff with optional jitter"""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        delay = min(self.base_delay * (self.multiplier**attempt), self.max_delay)

        if self.jitter:
            # Add random jitter (0-25% of delay)
            delay = delay * (1 + random.random() * 0.25)

        return delay


class LinearBackoff(RetryStrategy):
    """Linear backoff strategy"""

    def __init__(
        self, base_delay: float = 1.0, increment: float = 1.0, max_delay: float = 30.0
    ):
        self.base_delay = base_delay
        self.increment = increment
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        return min(self.base_delay + (attempt * self.increment), self.max_delay)


@dataclass
class RetryContext:
    """Context information for retry attempts"""

    attempt: int
    total_attempts: int
    elapsed_time: float
    last_exception: Optional[Exception]
    start_time: datetime


class RetryPolicy:
    """Configurable retry policy"""

    def __init__(
        self,
        max_attempts: int = 3,
        strategy: Optional[RetryStrategy] = None,
        retriable_exceptions: Optional[List[Type[Exception]]] = None,
        timeout: Optional[float] = None,
        on_retry: Optional[Callable[[RetryContext], None]] = None,
    ):
        """
        Initialize retry policy

        Args:
            max_attempts: Maximum number of attempts
            strategy: Retry delay strategy
            retriable_exceptions: Exceptions to retry on (None = all)
            timeout: Overall timeout in seconds
            on_retry: Callback called before each retry
        """
        self.max_attempts = max_attempts
        self.strategy = strategy or ExponentialBackoff()
        self.retriable_exceptions = retriable_exceptions
        self.timeout = timeout
        self.on_retry = on_retry

    def is_retriable(self, exception: Exception) -> bool:
        """Check if exception is retriable"""
        if self.retriable_exceptions is None:
            return True

        return any(
            isinstance(exception, exc_type) for exc_type in self.retriable_exceptions
        )

    async def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Execute function with retry policy

        Args:
            func: Async function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries failed
        """
        start_time = datetime.now()
        last_exception = None

        for attempt in range(self.max_attempts):
            # Check timeout
            if self.timeout:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > self.timeout:
                    raise TimeoutError(
                        f"Retry timeout after {elapsed:.1f}s " f"({attempt} attempts)"
                    )

            try:
                # Execute function
                result = await func(*args, **kwargs)

                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt + 1}")

                return result

            except Exception as e:
                last_exception = e

                # Check if should retry
                if not self.is_retriable(e) or attempt == self.max_attempts - 1:
                    raise

                # Calculate delay
                delay = self.strategy.get_delay(attempt)

                # Create context
                context = RetryContext(
                    attempt=attempt + 1,
                    total_attempts=self.max_attempts,
                    elapsed_time=(datetime.now() - start_time).total_seconds(),
                    last_exception=e,
                    start_time=start_time,
                )

                # Call retry callback
                if self.on_retry:
                    try:
                        self.on_retry(context)
                    except Exception as cb_error:
                        logger.error(f"Retry callback error: {cb_error}")

                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )

                # Wait before retry
                await asyncio.sleep(delay)

        # Should never reach here
        raise last_exception


# Decorator for easy retry usage
def retry(
    max_attempts: int = 3,
    strategy: Optional[RetryStrategy] = None,
    exceptions: Optional[List[Type[Exception]]] = None,
    timeout: Optional[float] = None,
):
    """
    Decorator to add retry logic to async function

    Example:
        @retry(max_attempts=3, strategy=ExponentialBackoff())
        async def flaky_function():
            ...
    """

    def decorator(func):
        policy = RetryPolicy(
            max_attempts=max_attempts,
            strategy=strategy,
            retriable_exceptions=exceptions,
            timeout=timeout,
        )

        async def wrapper(*args, **kwargs):
            return await policy.execute(func, *args, **kwargs)

        return wrapper

    return decorator


# Common retry policies
class RetryPolicies:
    """Common pre-configured retry policies"""

    @staticmethod
    def quick() -> RetryPolicy:
        """Quick retry for transient errors"""
        return RetryPolicy(max_attempts=3, strategy=FixedDelay(0.5), timeout=5.0)

    @staticmethod
    def standard() -> RetryPolicy:
        """Standard exponential backoff"""
        return RetryPolicy(
            max_attempts=5,
            strategy=ExponentialBackoff(base_delay=1.0, max_delay=30.0),
            timeout=120.0,
        )

    @staticmethod
    def aggressive() -> RetryPolicy:
        """Aggressive retry for critical operations"""
        return RetryPolicy(
            max_attempts=10,
            strategy=ExponentialBackoff(base_delay=0.5, max_delay=60.0),
            timeout=300.0,
        )

    @staticmethod
    def network() -> RetryPolicy:
        """Retry policy for network operations"""
        return RetryPolicy(
            max_attempts=5,
            strategy=ExponentialBackoff(base_delay=2.0, max_delay=30.0),
            retriable_exceptions=[ConnectionError, TimeoutError, asyncio.TimeoutError],
            timeout=60.0,
        )

    @staticmethod
    def database() -> RetryPolicy:
        """Retry policy for database operations"""
        return RetryPolicy(
            max_attempts=3,
            strategy=ExponentialBackoff(base_delay=0.5, max_delay=5.0),
            timeout=30.0,
        )
