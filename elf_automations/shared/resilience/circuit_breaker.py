"""
Circuit breaker pattern implementation

Prevents cascading failures by:
1. Monitoring failure rates
2. Opening circuit when threshold exceeded
3. Rejecting requests while open
4. Attempting recovery after timeout
5. Closing circuit on successful recovery
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable, Optional, Type

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests rejected
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
        name: Optional[str] = None,
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
            name: Optional name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name or "CircuitBreaker"

        # State tracking
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._state_changed_at = datetime.now()

        # Thread safety
        self._lock = Lock()

        # Metrics
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        self._rejected_calls = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            self._check_recovery()
            return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting requests)"""
        return self.state == CircuitState.OPEN

    def _check_recovery(self):
        """Check if circuit should attempt recovery"""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time:
                time_since_failure = datetime.now() - self._last_failure_time
                if time_since_failure > timedelta(seconds=self.recovery_timeout):
                    logger.info(
                        f"{self.name}: Attempting recovery (moving to HALF_OPEN)"
                    )
                    self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state"""
        old_state = self._state
        self._state = new_state
        self._state_changed_at = datetime.now()

        if new_state == CircuitState.CLOSED:
            self._failure_count = 0

        logger.info(
            f"{self.name}: State transition {old_state.value} -> {new_state.value}"
        )

    def _record_success(self):
        """Record successful call"""
        with self._lock:
            self._total_calls += 1
            self._total_successes += 1

            if self._state == CircuitState.HALF_OPEN:
                # Success in half-open state means recovery
                logger.info(f"{self.name}: Recovery successful, closing circuit")
                self._transition_to(CircuitState.CLOSED)

            # Reset failure count on success
            self._failure_count = 0

    def _record_failure(self):
        """Record failed call"""
        with self._lock:
            self._total_calls += 1
            self._total_failures += 1
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open means still broken
                logger.warning(f"{self.name}: Recovery failed, reopening circuit")
                self._transition_to(CircuitState.OPEN)

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    logger.error(
                        f"{self.name}: Failure threshold reached "
                        f"({self._failure_count}/{self.failure_threshold}), opening circuit"
                    )
                    self._transition_to(CircuitState.OPEN)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        # Check state
        if self.state == CircuitState.OPEN:
            self._rejected_calls += 1
            raise Exception(f"{self.name}: Circuit breaker is OPEN - request rejected")

        # Attempt call
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result

        except self.expected_exception as e:
            self._record_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call async function through circuit breaker

        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        # Check state
        if self.state == CircuitState.OPEN:
            self._rejected_calls += 1
            raise Exception(f"{self.name}: Circuit breaker is OPEN - request rejected")

        # Attempt call
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._record_success()
            return result

        except self.expected_exception as e:
            self._record_failure()
            raise

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        with self._lock:
            success_rate = 0
            if self._total_calls > 0:
                success_rate = (self._total_successes / self._total_calls) * 100

            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "total_calls": self._total_calls,
                "total_successes": self._total_successes,
                "total_failures": self._total_failures,
                "rejected_calls": self._rejected_calls,
                "success_rate": round(success_rate, 2),
                "state_changed_at": self._state_changed_at.isoformat(),
                "time_in_state": str(datetime.now() - self._state_changed_at),
            }

    def reset(self):
        """Reset circuit breaker to closed state"""
        with self._lock:
            logger.info(f"{self.name}: Manual reset to CLOSED state")
            self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._last_failure_time = None

    def trip(self):
        """Manually trip the circuit breaker to open state"""
        with self._lock:
            logger.warning(f"{self.name}: Manual trip to OPEN state")
            self._transition_to(CircuitState.OPEN)
            self._last_failure_time = datetime.now()
