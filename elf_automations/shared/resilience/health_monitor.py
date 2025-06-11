"""
Health monitoring for services and resources

Provides continuous health checks and aggregated health status
for all system components.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check configuration"""

    name: str
    check_func: Callable[[], bool]
    interval: int = 60  # seconds
    timeout: int = 10  # seconds
    critical: bool = True  # Whether this affects overall health


@dataclass
class HealthCheckResult:
    """Result of a health check"""

    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    duration: float  # seconds
    metadata: Optional[Dict[str, Any]] = None


class HealthMonitor:
    """Monitors health of system components"""

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        alert_callback: Optional[Callable[[HealthCheckResult], None]] = None,
    ):
        """
        Initialize health monitor

        Args:
            storage_path: Path to store health metrics
            alert_callback: Function to call on health alerts
        """
        self.storage_path = storage_path or (
            Path.home() / ".elf_automations" / "health_metrics"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.alert_callback = alert_callback

        # Registered health checks
        self._health_checks: Dict[str, HealthCheck] = {}

        # Latest results
        self._latest_results: Dict[str, HealthCheckResult] = {}

        # Background tasks
        self._tasks: Dict[str, asyncio.Task] = {}

        # Overall health cache
        self._overall_health = HealthStatus.UNKNOWN
        self._last_overall_check = datetime.now()

    def register_check(self, health_check: HealthCheck):
        """Register a health check"""
        self._health_checks[health_check.name] = health_check
        logger.info(f"Registered health check: {health_check.name}")

    def register_default_checks(self):
        """Register default system health checks"""

        # API health check
        async def check_api_health():
            try:
                from ..quota import QuotaManager

                qm = QuotaManager()
                # Check if we have any budget left
                budgets = [qm.get_team_budget(team) for team in qm.usage_data.keys()]
                return any(budget > 0 for budget in budgets)
            except:
                return False

        self.register_check(
            HealthCheck(
                name="api_quota",
                check_func=check_api_health,
                interval=300,  # 5 minutes
                critical=True,
            )
        )

        # Memory health check
        def check_memory_health():
            import psutil

            return psutil.virtual_memory().percent < 90

        self.register_check(
            HealthCheck(
                name="memory",
                check_func=check_memory_health,
                interval=60,
                critical=True,
            )
        )

        # CPU health check
        def check_cpu_health():
            import psutil

            return psutil.cpu_percent(interval=1) < 90

        self.register_check(
            HealthCheck(
                name="cpu", check_func=check_cpu_health, interval=60, critical=False
            )
        )

        # Disk health check
        def check_disk_health():
            import psutil

            return psutil.disk_usage("/").percent < 90

        self.register_check(
            HealthCheck(
                name="disk",
                check_func=check_disk_health,
                interval=300,  # 5 minutes
                critical=False,
            )
        )

    async def _run_health_check(self, check: HealthCheck) -> HealthCheckResult:
        """Run a single health check"""
        start_time = datetime.now()

        try:
            # Run check with timeout
            if asyncio.iscoroutinefunction(check.check_func):
                result = await asyncio.wait_for(
                    check.check_func(), timeout=check.timeout
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, check.check_func),
                    timeout=check.timeout,
                )

            duration = (datetime.now() - start_time).total_seconds()

            status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
            message = "Check passed" if result else "Check failed"

            return HealthCheckResult(
                name=check.name,
                status=status,
                message=message,
                timestamp=start_time,
                duration=duration,
            )

        except asyncio.TimeoutError:
            duration = (datetime.now() - start_time).total_seconds()
            return HealthCheckResult(
                name=check.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check timed out after {check.timeout}s",
                timestamp=start_time,
                duration=duration,
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return HealthCheckResult(
                name=check.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed with error: {str(e)}",
                timestamp=start_time,
                duration=duration,
            )

    async def _health_check_loop(self, check_name: str):
        """Background loop for a health check"""
        check = self._health_checks[check_name]

        while check_name in self._health_checks:
            try:
                # Run check
                result = await self._run_health_check(check)

                # Store result
                self._latest_results[check_name] = result

                # Log result
                self._log_result(result)

                # Alert if unhealthy and critical
                if result.status == HealthStatus.UNHEALTHY and check.critical:
                    if self.alert_callback:
                        self.alert_callback(result)
                    logger.error(
                        f"Critical health check failed: {check_name} - {result.message}"
                    )

                # Wait for next interval
                await asyncio.sleep(check.interval)

            except Exception as e:
                logger.error(f"Error in health check loop for {check_name}: {e}")
                await asyncio.sleep(check.interval)

    def _log_result(self, result: HealthCheckResult):
        """Log health check result to file"""
        log_entry = {
            "timestamp": result.timestamp.isoformat(),
            "name": result.name,
            "status": result.status.value,
            "message": result.message,
            "duration": result.duration,
            "metadata": result.metadata,
        }

        log_file = self.storage_path / f"{result.name}_health.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def start_monitoring(self):
        """Start all health check loops"""
        for check_name in self._health_checks:
            if check_name not in self._tasks:
                task = asyncio.create_task(self._health_check_loop(check_name))
                self._tasks[check_name] = task

        logger.info(f"Started monitoring {len(self._tasks)} health checks")

    async def stop_monitoring(self):
        """Stop all health check loops"""
        for task in self._tasks.values():
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)

        self._tasks.clear()
        logger.info("Stopped health monitoring")

    def get_health_status(self, check_name: Optional[str] = None) -> HealthStatus:
        """
        Get health status

        Args:
            check_name: Specific check name, or None for overall health

        Returns:
            Health status
        """
        if check_name:
            if check_name in self._latest_results:
                return self._latest_results[check_name].status
            return HealthStatus.UNKNOWN

        # Calculate overall health
        now = datetime.now()
        if now - self._last_overall_check < timedelta(seconds=10):
            return self._overall_health

        # Recalculate
        if not self._latest_results:
            self._overall_health = HealthStatus.UNKNOWN
        else:
            # Check critical services
            critical_checks = [
                name for name, check in self._health_checks.items() if check.critical
            ]

            critical_statuses = [
                self._latest_results.get(
                    name,
                    HealthCheckResult(
                        name=name,
                        status=HealthStatus.UNKNOWN,
                        message="No result yet",
                        timestamp=now,
                        duration=0,
                    ),
                ).status
                for name in critical_checks
            ]

            if any(s == HealthStatus.UNHEALTHY for s in critical_statuses):
                self._overall_health = HealthStatus.UNHEALTHY
            elif any(s == HealthStatus.DEGRADED for s in critical_statuses):
                self._overall_health = HealthStatus.DEGRADED
            elif all(s == HealthStatus.HEALTHY for s in critical_statuses):
                self._overall_health = HealthStatus.HEALTHY
            else:
                self._overall_health = HealthStatus.UNKNOWN

        self._last_overall_check = now
        return self._overall_health

    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self.get_health_status().value,
            "checks": {},
        }

        for check_name, result in self._latest_results.items():
            report["checks"][check_name] = {
                "status": result.status.value,
                "message": result.message,
                "last_check": result.timestamp.isoformat(),
                "duration": result.duration,
                "critical": self._health_checks[check_name].critical,
            }

        # Add checks that haven't run yet
        for check_name in self._health_checks:
            if check_name not in report["checks"]:
                report["checks"][check_name] = {
                    "status": HealthStatus.UNKNOWN.value,
                    "message": "Check not yet run",
                    "critical": self._health_checks[check_name].critical,
                }

        return report

    async def run_check_now(self, check_name: str) -> HealthCheckResult:
        """Run a specific health check immediately"""
        if check_name not in self._health_checks:
            raise ValueError(f"Unknown health check: {check_name}")

        result = await self._run_health_check(self._health_checks[check_name])
        self._latest_results[check_name] = result
        self._log_result(result)

        return result
