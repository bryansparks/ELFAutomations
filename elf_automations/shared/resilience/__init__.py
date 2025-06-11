"""
Resilience framework for resource management and fallback protocols

Provides comprehensive fallback strategies for:
- API quotas and rate limits
- Memory and compute resources
- Database connections
- MCP server availability
- Network endpoints
- Docker/K8s resources
"""

from .circuit_breaker import CircuitBreaker, CircuitState
from .fallback_protocols import (
    FallbackProtocol,
    FallbackStrategy,
    with_circuit_breaker,
    with_fallback,
    with_retry,
)
from .health_monitor import HealthMonitor, HealthStatus
from .resource_manager import ResourceManager, ResourceStatus, ResourceType
from .retry_policies import ExponentialBackoff, FixedDelay, LinearBackoff, RetryPolicy

__all__ = [
    # Resource Management
    "ResourceManager",
    "ResourceType",
    "ResourceStatus",
    # Fallback Protocols
    "FallbackProtocol",
    "FallbackStrategy",
    "with_fallback",
    "with_retry",
    "with_circuit_breaker",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    # Retry Policies
    "RetryPolicy",
    "ExponentialBackoff",
    "LinearBackoff",
    "FixedDelay",
    # Health Monitoring
    "HealthMonitor",
    "HealthStatus",
]
