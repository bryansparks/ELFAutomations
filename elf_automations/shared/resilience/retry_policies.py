"""
Retry policies for resilient operations

Provides various backoff strategies:
- Exponential backoff
- Linear backoff
- Fixed delay
- Jittered backoff
"""

import logging
import random
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class RetryPolicy(ABC):
    """Abstract base class for retry policies"""

    def __init__(
        self, max_retries: int = 3, max_delay: float = 60.0, jitter: bool = True
    ):
        """
        Initialize retry policy

        Args:
            max_retries: Maximum number of retry attempts
            max_delay: Maximum delay between retries (seconds)
            jitter: Whether to add random jitter to delays
        """
        self.max_retries = max_retries
        self.max_delay = max_delay
        self.jitter = jitter

    @abstractmethod
    def get_base_delay(self, attempt: int) -> float:
        """Get base delay for given attempt number"""
        pass

    def get_delay(self, attempt: int) -> float:
        """
        Get delay with jitter for given attempt

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        base_delay = self.get_base_delay(attempt)

        # Cap at max delay
        delay = min(base_delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter and delay > 0:
            # Add random jitter between -25% and +25%
            jitter_range = delay * 0.25
            jitter_amount = random.uniform(-jitter_range, jitter_range)
            delay += jitter_amount

        return max(0, delay)  # Ensure non-negative

    def should_retry(self, attempt: int, exception: Optional[Exception] = None) -> bool:
        """
        Determine if should retry

        Args:
            attempt: Current attempt number (0-based)
            exception: Exception that occurred

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False

        # Could add logic to check exception type
        return True


class ExponentialBackoff(RetryPolicy):
    """
    Exponential backoff retry policy

    Delay doubles with each attempt: 1s, 2s, 4s, 8s, ...
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        multiplier: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True,
    ):
        """
        Initialize exponential backoff

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay (seconds)
            multiplier: Delay multiplier for each attempt
            max_delay: Maximum delay between retries
            jitter: Whether to add random jitter
        """
        super().__init__(max_retries, max_delay, jitter)
        self.base_delay = base_delay
        self.multiplier = multiplier

    def get_base_delay(self, attempt: int) -> float:
        """Calculate exponential delay"""
        return self.base_delay * (self.multiplier**attempt)


class LinearBackoff(RetryPolicy):
    """
    Linear backoff retry policy

    Delay increases linearly: 1s, 2s, 3s, 4s, ...
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        increment: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
    ):
        """
        Initialize linear backoff

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay (seconds)
            increment: Delay increment for each attempt
            max_delay: Maximum delay between retries
            jitter: Whether to add random jitter
        """
        super().__init__(max_retries, max_delay, jitter)
        self.base_delay = base_delay
        self.increment = increment

    def get_base_delay(self, attempt: int) -> float:
        """Calculate linear delay"""
        return self.base_delay + (self.increment * attempt)


class FixedDelay(RetryPolicy):
    """
    Fixed delay retry policy

    Same delay for all attempts
    """

    def __init__(self, max_retries: int = 3, delay: float = 1.0, jitter: bool = False):
        """
        Initialize fixed delay

        Args:
            max_retries: Maximum number of retry attempts
            delay: Fixed delay between retries (seconds)
            jitter: Whether to add random jitter
        """
        super().__init__(max_retries, delay, jitter)
        self.delay = delay

    def get_base_delay(self, attempt: int) -> float:
        """Return fixed delay"""
        return self.delay


class FibonacciBackoff(RetryPolicy):
    """
    Fibonacci sequence backoff retry policy

    Delay follows Fibonacci sequence: 1s, 1s, 2s, 3s, 5s, 8s, ...
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
    ):
        """
        Initialize Fibonacci backoff

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay multiplier (seconds)
            max_delay: Maximum delay between retries
            jitter: Whether to add random jitter
        """
        super().__init__(max_retries, max_delay, jitter)
        self.base_delay = base_delay

        # Pre-calculate Fibonacci numbers
        self._fib_cache = [1, 1]
        for i in range(2, max_retries + 1):
            self._fib_cache.append(self._fib_cache[i - 1] + self._fib_cache[i - 2])

    def get_base_delay(self, attempt: int) -> float:
        """Calculate Fibonacci delay"""
        if attempt < len(self._fib_cache):
            return self.base_delay * self._fib_cache[attempt]
        return self.max_delay


class AdaptiveBackoff(RetryPolicy):
    """
    Adaptive backoff that adjusts based on error rate

    Increases delay when seeing many errors, decreases when successful
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        success_reduction: float = 0.5,
        failure_increase: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize adaptive backoff

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Starting delay (seconds)
            max_delay: Maximum delay between retries
            success_reduction: Factor to reduce delay on success
            failure_increase: Factor to increase delay on failure
            jitter: Whether to add random jitter
        """
        super().__init__(max_retries, max_delay, jitter)
        self.initial_delay = initial_delay
        self.success_reduction = success_reduction
        self.failure_increase = failure_increase

        # Track current delay
        self._current_delay = initial_delay

    def get_base_delay(self, attempt: int) -> float:
        """Get current adaptive delay"""
        return self._current_delay

    def record_success(self):
        """Record successful attempt and reduce delay"""
        self._current_delay *= self.success_reduction
        self._current_delay = max(self.initial_delay, self._current_delay)

    def record_failure(self):
        """Record failed attempt and increase delay"""
        self._current_delay *= self.failure_increase
        self._current_delay = min(self.max_delay, self._current_delay)
