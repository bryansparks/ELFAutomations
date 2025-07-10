"""
Infrastructure health checking and verification

Provides comprehensive health checks for:
- Kubernetes deployments
- Docker containers
- Database connections
- API endpoints
- System resources
"""

import asyncio
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import psutil

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""

    name: str
    component_type: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY


class HealthChecker:
    """Comprehensive infrastructure health checker"""

    def __init__(self, k8s_context: str = "docker-desktop"):
        """
        Initialize health checker

        Args:
            k8s_context: Kubernetes context to use
        """
        self.k8s_context = k8s_context
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        results = {}

        # System health
        results["system"] = await self.check_system_health()

        # Docker health
        results["docker"] = await self.check_docker_health()

        # Kubernetes health
        results["kubernetes"] = await self.check_kubernetes_health()

        # Database health (if configured)
        results["database"] = await self.check_database_health()

        return results

    async def check_system_health(self) -> HealthCheckResult:
        """Check system resource health"""
        try:
            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=1)

            # Check memory
            memory = psutil.virtual_memory()

            # Check disk
            disk = psutil.disk_usage("/")

            # Determine status
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "System resources critical"
            elif cpu_percent > 75 or memory.percent > 75 or disk.percent > 85:
                status = HealthStatus.DEGRADED
                message = "System resources high"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources normal"

            return HealthCheckResult(
                name="system",
                component_type="system",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3),
                },
            )

        except Exception as e:
            return HealthCheckResult(
                name="system",
                component_type="system",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check system health: {e}",
                timestamp=datetime.now(),
            )

    async def check_docker_health(self) -> HealthCheckResult:
        """Check Docker daemon health"""
        try:
            # Check Docker daemon
            result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                return HealthCheckResult(
                    name="docker",
                    component_type="docker",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Docker daemon not accessible: {result.stderr}",
                    timestamp=datetime.now(),
                )

            # Check registry if configured
            registry_healthy = await self._check_docker_registry()

            if not registry_healthy:
                return HealthCheckResult(
                    name="docker",
                    component_type="docker",
                    status=HealthStatus.DEGRADED,
                    message="Docker healthy but registry not accessible",
                    timestamp=datetime.now(),
                )

            return HealthCheckResult(
                name="docker",
                component_type="docker",
                status=HealthStatus.HEALTHY,
                message="Docker daemon and registry healthy",
                timestamp=datetime.now(),
            )

        except subprocess.TimeoutExpired:
            return HealthCheckResult(
                name="docker",
                component_type="docker",
                status=HealthStatus.UNHEALTHY,
                message="Docker daemon timeout",
                timestamp=datetime.now(),
            )
        except Exception as e:
            return HealthCheckResult(
                name="docker",
                component_type="docker",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check Docker health: {e}",
                timestamp=datetime.now(),
            )

    async def _check_docker_registry(self) -> bool:
        """Check if Docker registry is accessible"""
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()

            async with self._session.get("http://localhost:5000/v2/") as response:
                return response.status == 200
        except:
            return False

    async def check_kubernetes_health(self) -> HealthCheckResult:
        """Check Kubernetes cluster health"""
        try:
            # Check cluster info
            result = subprocess.run(
                ["kubectl", "cluster-info", "--context", self.k8s_context],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return HealthCheckResult(
                    name="kubernetes",
                    component_type="kubernetes",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Kubernetes cluster not accessible: {result.stderr}",
                    timestamp=datetime.now(),
                )

            # Check nodes
            nodes_result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "nodes",
                    "--context",
                    self.k8s_context,
                    "-o",
                    "json",
                ],
                capture_output=True,
                text=True,
            )

            if nodes_result.returncode == 0:
                import json

                nodes_data = json.loads(nodes_result.stdout)
                ready_nodes = sum(
                    1
                    for node in nodes_data.get("items", [])
                    if any(
                        condition["type"] == "Ready" and condition["status"] == "True"
                        for condition in node["status"].get("conditions", [])
                    )
                )
                total_nodes = len(nodes_data.get("items", []))

                if ready_nodes < total_nodes:
                    return HealthCheckResult(
                        name="kubernetes",
                        component_type="kubernetes",
                        status=HealthStatus.DEGRADED,
                        message=f"Only {ready_nodes}/{total_nodes} nodes ready",
                        timestamp=datetime.now(),
                        details={
                            "ready_nodes": ready_nodes,
                            "total_nodes": total_nodes,
                        },
                    )

            return HealthCheckResult(
                name="kubernetes",
                component_type="kubernetes",
                status=HealthStatus.HEALTHY,
                message="Kubernetes cluster healthy",
                timestamp=datetime.now(),
            )

        except subprocess.TimeoutExpired:
            return HealthCheckResult(
                name="kubernetes",
                component_type="kubernetes",
                status=HealthStatus.UNHEALTHY,
                message="Kubernetes command timeout",
                timestamp=datetime.now(),
            )
        except Exception as e:
            return HealthCheckResult(
                name="kubernetes",
                component_type="kubernetes",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check Kubernetes health: {e}",
                timestamp=datetime.now(),
            )

    async def check_database_health(self) -> HealthCheckResult:
        """Check database health"""
        try:
            # Try to import Supabase
            import os

            from supabase import create_client

            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")

            if not url or not key:
                return HealthCheckResult(
                    name="database",
                    component_type="database",
                    status=HealthStatus.UNKNOWN,
                    message="Database not configured",
                    timestamp=datetime.now(),
                )

            # Try a simple query
            client = create_client(url, key)
            result = (
                client.table("schema_migrations")
                .select("count", count="exact")
                .execute()
            )

            return HealthCheckResult(
                name="database",
                component_type="database",
                status=HealthStatus.HEALTHY,
                message="Database connection healthy",
                timestamp=datetime.now(),
                details={
                    "table_count": result.count if hasattr(result, "count") else 0
                },
            )

        except Exception as e:
            return HealthCheckResult(
                name="database",
                component_type="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {e}",
                timestamp=datetime.now(),
            )

    async def check_deployment_health(
        self, deployment_name: str, namespace: str = "elf-teams"
    ) -> HealthCheckResult:
        """Check specific Kubernetes deployment health"""
        try:
            # Get deployment status
            cmd = [
                "kubectl",
                "get",
                "deployment",
                deployment_name,
                "-n",
                namespace,
                "--context",
                self.k8s_context,
                "-o",
                "json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return HealthCheckResult(
                    name=f"deployment/{deployment_name}",
                    component_type="deployment",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Deployment not found: {result.stderr}",
                    timestamp=datetime.now(),
                )

            import json

            deployment = json.loads(result.stdout)
            status = deployment.get("status", {})

            replicas = status.get("replicas", 0)
            ready_replicas = status.get("readyReplicas", 0)

            if ready_replicas == 0:
                health_status = HealthStatus.UNHEALTHY
                message = "No ready replicas"
            elif ready_replicas < replicas:
                health_status = HealthStatus.DEGRADED
                message = f"Only {ready_replicas}/{replicas} replicas ready"
            else:
                health_status = HealthStatus.HEALTHY
                message = f"All {replicas} replicas ready"

            return HealthCheckResult(
                name=f"deployment/{deployment_name}",
                component_type="deployment",
                status=health_status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "replicas": replicas,
                    "ready_replicas": ready_replicas,
                    "namespace": namespace,
                },
            )

        except Exception as e:
            return HealthCheckResult(
                name=f"deployment/{deployment_name}",
                component_type="deployment",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check deployment: {e}",
                timestamp=datetime.now(),
            )

    async def check_endpoint(
        self, url: str, expected_status: int = 200, timeout: int = 10
    ) -> Dict[str, Any]:
        """Check HTTP endpoint health"""
        if not self._session:
            self._session = aiohttp.ClientSession()

        try:
            async with self._session.get(url, timeout=timeout) as response:
                is_healthy = response.status == expected_status

                return {
                    "healthy": is_healthy,
                    "status_code": response.status,
                    "response_time": timeout,  # Would need proper timing
                    "url": url,
                }

        except asyncio.TimeoutError:
            return {"healthy": False, "error": "Timeout", "url": url}
        except Exception as e:
            return {"healthy": False, "error": str(e), "url": url}

    async def wait_for_healthy(
        self, check_func: Callable, timeout: int = 300, interval: int = 5
    ) -> bool:
        """
        Wait for a health check to become healthy

        Args:
            check_func: Async function that returns HealthCheckResult
            timeout: Maximum time to wait (seconds)
            interval: Check interval (seconds)

        Returns:
            True if became healthy, False if timeout
        """
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < timeout:
            result = await check_func()

            if result.is_healthy:
                logger.info(f"{result.name} is now healthy")
                return True

            logger.debug(f"{result.name} still {result.status.value}: {result.message}")
            await asyncio.sleep(interval)

        return False


class InfrastructureHealth:
    """Overall infrastructure health assessment"""

    def __init__(self, health_checker: HealthChecker):
        """
        Initialize infrastructure health

        Args:
            health_checker: HealthChecker instance
        """
        self.checker = health_checker

    async def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive infrastructure health report"""

        # Run all checks
        results = await self.checker.check_all()

        # Calculate overall health
        statuses = [r.status for r in results.values()]

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall = HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        else:
            overall = HealthStatus.UNKNOWN

        # Build report
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall.value,
            "components": {},
        }

        for name, result in results.items():
            report["components"][name] = {
                "status": result.status.value,
                "message": result.message,
                "details": result.details,
            }

        return report

    async def monitor_continuously(
        self, interval: int = 60, callback: Optional[Callable] = None
    ):
        """
        Monitor infrastructure health continuously

        Args:
            interval: Check interval in seconds
            callback: Optional callback for health updates
        """
        while True:
            try:
                report = await self.get_health_report()

                if callback:
                    await callback(report) if asyncio.iscoroutinefunction(
                        callback
                    ) else callback(report)

                # Log status
                logger.info(f"Infrastructure health: {report['overall_status']}")

                # Wait for next check
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(interval)
