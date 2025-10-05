"""Circuit breaker pattern implementation for external service calls.

This module provides a robust circuit breaker implementation to handle
failures gracefully and prevent cascading failures in distributed systems.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """States for the circuit breaker."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    expected_exception: tuple = (Exception,)
    success_threshold: int = 3
    timeout: float = 30.0  # seconds for individual calls


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: list = field(default_factory=list)


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, name: str, retry_after: float):
        self.name = name
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker '{name}' is open. Retry after {retry_after:.1f} seconds")


class AsyncCircuitBreaker:
    """Async circuit breaker implementation."""

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    async def _should_attempt_call(self) -> bool:
        """Determine if we should attempt the call based on current state."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if time.time() - (self.stats.last_failure_time or 0) > self.config.recovery_timeout:
                async with self._lock:
                    if self.state == CircuitBreakerState.OPEN:
                        self.state = CircuitBreakerState.HALF_OPEN
                        self.stats.state_changes.append({
                            'from': 'open',
                            'to': 'half_open',
                            'timestamp': time.time()
                        })
                        logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                        return True
            return False
        else:  # HALF_OPEN
            return True

    async def _record_success(self):
        """Record a successful call."""
        self.stats.total_calls += 1
        self.stats.successful_calls += 1
        self.stats.consecutive_failures = 0
        self.stats.consecutive_successes += 1
        self.stats.last_success_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN and self.stats.consecutive_successes >= self.config.success_threshold:
            async with self._lock:
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self.state = CircuitBreakerState.CLOSED
                    self.stats.state_changes.append({
                        'from': 'half_open',
                        'to': 'closed',
                        'timestamp': time.time()
                    })
                    logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED")

    async def _record_failure(self, exception: Exception):
        """Record a failed call."""
        self.stats.total_calls += 1
        self.stats.failed_calls += 1
        self.stats.consecutive_failures += 1
        self.stats.consecutive_successes = 0
        self.stats.last_failure_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            async with self._lock:
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self.state = CircuitBreakerState.OPEN
                    self.stats.state_changes.append({
                        'from': 'half_open',
                        'to': 'open',
                        'timestamp': time.time()
                    })
                    logger.warning(f"Circuit breaker '{self.name}' transitioning to OPEN after half-open failure")

        elif self.state == CircuitBreakerState.CLOSED and self.stats.consecutive_failures >= self.config.failure_threshold:
            async with self._lock:
                if self.state == CircuitBreakerState.CLOSED:
                    self.state = CircuitBreakerState.OPEN
                    self.stats.state_changes.append({
                        'from': 'closed',
                        'to': 'open',
                        'timestamp': time.time()
                    })
                    logger.warning(f"Circuit breaker '{self.name}' transitioning to OPEN after {self.stats.consecutive_failures} failures")

    @asynccontextmanager
    async def _call_context(self):
        """Context manager for call execution."""
        should_call = await self._should_attempt_call()

        if not should_call:
            raise CircuitBreakerOpenException(
                self.name,
                self.config.recovery_timeout - (time.time() - (self.stats.last_failure_time or 0))
            )

        try:
            yield
        except self.config.expected_exception as e:
            await self._record_failure(e)
            raise
        else:
            await self._record_success()

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        async with self._call_context():
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return await asyncio.get_event_loop().run_in_executor(None, func, *args, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            'name': self.name,
            'state': self.state.value,
            'stats': {
                'total_calls': self.stats.total_calls,
                'successful_calls': self.stats.successful_calls,
                'failed_calls': self.stats.failed_calls,
                'consecutive_failures': self.stats.consecutive_failures,
                'consecutive_successes': self.stats.consecutive_successes,
                'last_failure_time': self.stats.last_failure_time,
                'last_success_time': self.stats.last_success_time,
                'state_changes': self.stats.state_changes
            }
        }


class RetryPolicy:
    """Retry policy for failed operations."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = min(self.base_delay * (self.backoff_factor ** (attempt - 1)), self.max_delay)

        if self.jitter:
            # Add random jitter to prevent thundering herd
            import random
            delay *= (0.5 + random.random() * 0.5)

        return delay


async def retry_async(
    func: Callable[..., T],
    policy: RetryPolicy,
    exceptions: tuple = (Exception,),
    *args,
    **kwargs
) -> T:
    """Retry async function with exponential backoff."""
    last_exception = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e

            if attempt == policy.max_attempts:
                logger.error(f"Function {func.__name__} failed after {policy.max_attempts} attempts")
                raise

            delay = policy.calculate_delay(attempt)
            logger.warning(f"Attempt {attempt} failed for {func.__name__}, retrying in {delay:.1f}s: {e}")
            await asyncio.sleep(delay)

    # This should never be reached, but just in case
    raise last_exception


# Global circuit breaker registry
_circuit_breakers: Dict[str, AsyncCircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> AsyncCircuitBreaker:
    """Get or create a circuit breaker instance."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = AsyncCircuitBreaker(name, config)
    return _circuit_breakers[name]


def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all circuit breakers."""
    return {name: cb.get_stats() for name, cb in _circuit_breakers.items()}