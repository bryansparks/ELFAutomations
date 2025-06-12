"""
Health check functionality for distributed agents.
Provides Kubernetes-compatible health and readiness probes.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    STARTING = "starting"
    STOPPING = "stopping"


class HealthCheckMixin:
    """
    Mixin class providing health check functionality for distributed agents.
    Compatible with Kubernetes liveness and readiness probes.
    """

    def __init__(self):
        """Initialize health check system."""
        self.health_status = HealthStatus.STARTING
        self.health_checks_enabled = False
        self.last_health_check = None
        self.health_check_interval = 30  # seconds
        self.health_check_task: Optional[asyncio.Task] = None

        # Health metrics
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        self.health_check_history: list = []
        self.max_history_size = 100

        self.logger = logging.getLogger(f"{self.__class__.__name__}.health")

    def start_health_checks(self) -> None:
        """Start the health check monitoring system."""
        if not self.health_checks_enabled:
            self.health_checks_enabled = True
            self.health_status = HealthStatus.HEALTHY
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            self.logger.info("Health checks started")

    def stop_health_checks(self) -> None:
        """Stop the health check monitoring system."""
        self.health_checks_enabled = False
        self.health_status = HealthStatus.STOPPING

        if self.health_check_task:
            self.health_check_task.cancel()
            self.health_check_task = None

        self.logger.info("Health checks stopped")

    async def _health_check_loop(self) -> None:
        """Main health check loop."""
        while self.health_checks_enabled:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self.health_check_interval)

    async def _perform_health_check(self) -> None:
        """Perform a single health check."""
        try:
            check_time = datetime.utcnow()

            # Perform various health checks
            checks = {
                "agent_running": await self._check_agent_running(),
                "a2a_connectivity": await self._check_a2a_connectivity(),
                "memory_usage": await self._check_memory_usage(),
                "task_processing": await self._check_task_processing(),
                "message_handling": await self._check_message_handling(),
            }

            # Determine overall health
            failed_checks = [name for name, status in checks.items() if not status]

            if not failed_checks:
                self.health_status = HealthStatus.HEALTHY
                self.consecutive_failures = 0
            elif len(failed_checks) <= 1:
                self.health_status = HealthStatus.DEGRADED
                self.consecutive_failures += 1
            else:
                self.health_status = HealthStatus.UNHEALTHY
                self.consecutive_failures += 1

            # Record health check result
            health_record = {
                "timestamp": check_time.isoformat(),
                "status": self.health_status.value,
                "checks": checks,
                "failed_checks": failed_checks,
                "consecutive_failures": self.consecutive_failures,
            }

            self._record_health_check(health_record)
            self.last_health_check = check_time

            # Log health status changes
            if failed_checks:
                self.logger.warning(
                    f"Health check failed: {failed_checks}, status: {self.health_status.value}"
                )
            else:
                self.logger.debug(f"Health check passed: {self.health_status.value}")

        except Exception as e:
            self.logger.error(f"Health check failed with exception: {e}")
            self.health_status = HealthStatus.UNHEALTHY
            self.consecutive_failures += 1

    async def _check_agent_running(self) -> bool:
        """Check if the agent is running properly."""
        try:
            # Check if agent has required attributes and is in running state
            return hasattr(self, "is_running") and getattr(self, "is_running", False)
        except Exception:
            return False

    async def _check_a2a_connectivity(self) -> bool:
        """Check A2A communication connectivity."""
        try:
            # Check if A2A client manager is available and responsive
            if hasattr(self, "a2a_client_manager"):
                return await self.a2a_client_manager.health_check()
            return True  # No A2A manager means this check passes
        except Exception:
            return False

    async def _check_memory_usage(self) -> bool:
        """Check memory usage is within acceptable limits."""
        try:
            import psutil

            process = psutil.Process()
            memory_percent = process.memory_percent()

            # Fail if using more than 90% of available memory
            return memory_percent < 90.0
        except ImportError:
            # psutil not available, skip this check
            return True
        except Exception:
            return False

    async def _check_task_processing(self) -> bool:
        """Check if task processing is working."""
        try:
            # Check if agent can process tasks (basic functionality test)
            if hasattr(self, "crew_agent"):
                return self.crew_agent is not None
            return True
        except Exception:
            return False

    async def _check_message_handling(self) -> bool:
        """Check if message handling is working."""
        try:
            # Check if message handling infrastructure is available
            return hasattr(self, "handle_message") and callable(
                getattr(self, "handle_message")
            )
        except Exception:
            return False

    def _record_health_check(self, health_record: Dict[str, Any]) -> None:
        """Record a health check result in history."""
        self.health_check_history.append(health_record)

        # Trim history to max size
        if len(self.health_check_history) > self.max_history_size:
            self.health_check_history = self.health_check_history[
                -self.max_history_size :
            ]

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status for Kubernetes probes."""
        return {
            "status": self.health_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "last_check": self.last_health_check.isoformat()
            if self.last_health_check
            else None,
            "consecutive_failures": self.consecutive_failures,
            "checks_enabled": self.health_checks_enabled,
        }

    def is_healthy(self) -> bool:
        """Check if agent is currently healthy."""
        return self.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    def is_ready(self) -> bool:
        """Check if agent is ready to serve requests (Kubernetes readiness probe)."""
        return (
            self.health_status == HealthStatus.HEALTHY
            and self.consecutive_failures < self.max_consecutive_failures
            and hasattr(self, "is_running")
            and getattr(self, "is_running", False)
        )

    def is_live(self) -> bool:
        """Check if agent is alive (Kubernetes liveness probe)."""
        return self.health_status != HealthStatus.UNHEALTHY

    def get_health_history(self, limit: Optional[int] = None) -> list:
        """Get health check history."""
        history = self.health_check_history
        if limit:
            history = history[-limit:]
        return history
