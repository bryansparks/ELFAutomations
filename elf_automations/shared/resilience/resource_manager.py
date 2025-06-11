"""
Central resource manager for tracking and managing system resources

Monitors resource usage and availability across:
- API quotas
- Memory/CPU
- Database connections
- Network endpoints
- Docker/K8s resources
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import psutil

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources to monitor"""

    API_QUOTA = "api_quota"
    MEMORY = "memory"
    CPU = "cpu"
    DATABASE = "database"
    MCP_SERVER = "mcp_server"
    NETWORK = "network"
    DOCKER = "docker"
    K8S_POD = "k8s_pod"


class ResourceStatus(Enum):
    """Resource availability status"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    EXHAUSTED = "exhausted"


class ResourceManager:
    """Manages and monitors system resources"""

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        warning_thresholds: Optional[Dict[ResourceType, float]] = None,
        critical_thresholds: Optional[Dict[ResourceType, float]] = None,
    ):
        """
        Initialize resource manager

        Args:
            storage_path: Path to store resource metrics
            warning_thresholds: Warning threshold percentages (0-100)
            critical_thresholds: Critical threshold percentages (0-100)
        """
        self.storage_path = storage_path or (
            Path.home() / ".elf_automations" / "resource_metrics"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Default thresholds
        self.warning_thresholds = warning_thresholds or {
            ResourceType.API_QUOTA: 80,  # 80% of quota used
            ResourceType.MEMORY: 75,  # 75% memory used
            ResourceType.CPU: 80,  # 80% CPU used
            ResourceType.DATABASE: 90,  # 90% of connection pool
            ResourceType.DOCKER: 85,  # 85% of container limits
        }

        self.critical_thresholds = critical_thresholds or {
            ResourceType.API_QUOTA: 95,  # 95% of quota used
            ResourceType.MEMORY: 90,  # 90% memory used
            ResourceType.CPU: 95,  # 95% CPU used
            ResourceType.DATABASE: 95,  # 95% of connection pool
            ResourceType.DOCKER: 95,  # 95% of container limits
        }

        # Resource usage cache
        self._usage_cache = {}
        self._last_check = {}

    def check_resource(
        self, resource_type: ResourceType, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ResourceStatus, float]:
        """
        Check the status of a resource

        Args:
            resource_type: Type of resource to check
            context: Additional context (e.g., team_name, model_name)

        Returns:
            Tuple of (status, usage_percentage)
        """
        # Check cache first
        cache_key = f"{resource_type.value}:{json.dumps(context or {}, sort_keys=True)}"
        now = datetime.now()

        if cache_key in self._last_check:
            if now - self._last_check[cache_key] < timedelta(seconds=60):
                return self._usage_cache.get(cache_key, (ResourceStatus.HEALTHY, 0))

        # Get fresh data
        usage_pct = self._get_resource_usage(resource_type, context)
        status = self._determine_status(resource_type, usage_pct)

        # Cache results
        self._usage_cache[cache_key] = (status, usage_pct)
        self._last_check[cache_key] = now

        # Log if not healthy
        if status != ResourceStatus.HEALTHY:
            logger.warning(
                f"Resource {resource_type.value} is {status.value}: "
                f"{usage_pct:.1f}% used"
            )

        return status, usage_pct

    def _get_resource_usage(
        self, resource_type: ResourceType, context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Get current usage percentage for a resource"""

        if resource_type == ResourceType.MEMORY:
            return psutil.virtual_memory().percent

        elif resource_type == ResourceType.CPU:
            return psutil.cpu_percent(interval=0.1)

        elif resource_type == ResourceType.API_QUOTA:
            # Check with quota manager
            if context and "team_name" in context:
                from ..quota import QuotaManager

                quota_path = Path.home() / ".elf_automations" / "quota_data"
                qm = QuotaManager(storage_path=quota_path)

                budget = qm.get_team_budget(context["team_name"])
                today = datetime.now().strftime("%Y-%m-%d")

                usage = 0
                if context["team_name"] in qm.usage_data:
                    if today in qm.usage_data[context["team_name"]]:
                        usage = qm.usage_data[context["team_name"]][today]["total_cost"]

                return (usage / budget) * 100 if budget > 0 else 0
            return 0

        elif resource_type == ResourceType.DATABASE:
            # This would check actual DB connection pool
            # For now, return a dummy value
            return 50

        elif resource_type == ResourceType.DOCKER:
            # Check Docker stats if available
            try:
                import docker

                client = docker.from_env()
                # Get container stats
                containers = client.containers.list()
                if containers:
                    # Simple average of memory usage
                    total_usage = 0
                    for container in containers:
                        stats = container.stats(stream=False)
                        if "memory_stats" in stats:
                            usage = stats["memory_stats"].get("usage", 0)
                            limit = stats["memory_stats"].get("limit", 1)
                            total_usage += (usage / limit) * 100
                    return total_usage / len(containers)
            except:
                pass
            return 0

        else:
            # Default for unimplemented resources
            return 0

    def _determine_status(
        self, resource_type: ResourceType, usage_pct: float
    ) -> ResourceStatus:
        """Determine resource status based on usage percentage"""

        if usage_pct >= 100:
            return ResourceStatus.EXHAUSTED
        elif usage_pct >= self.critical_thresholds.get(resource_type, 95):
            return ResourceStatus.CRITICAL
        elif usage_pct >= self.warning_thresholds.get(resource_type, 80):
            return ResourceStatus.WARNING
        else:
            return ResourceStatus.HEALTHY

    def can_use_resource(
        self, resource_type: ResourceType, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a resource can be used

        Args:
            resource_type: Type of resource
            context: Additional context

        Returns:
            True if resource is available, False otherwise
        """
        status, _ = self.check_resource(resource_type, context)
        return status not in [ResourceStatus.EXHAUSTED, ResourceStatus.CRITICAL]

    def get_alternative_resource(
        self, resource_type: ResourceType, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get alternative resource when primary is unavailable

        Args:
            resource_type: Type of resource that's unavailable
            context: Current context

        Returns:
            Alternative resource configuration or None
        """
        if resource_type == ResourceType.API_QUOTA:
            # Suggest alternative model
            if context and "model" in context:
                current_model = context["model"]
                # Model fallback chain
                alternatives = {
                    "gpt-4": "gpt-3.5-turbo",
                    "gpt-3.5-turbo": "claude-3-haiku-20240307",
                    "claude-3-opus-20240229": "claude-3-sonnet-20240229",
                    "claude-3-sonnet-20240229": "claude-3-haiku-20240307",
                }
                if current_model in alternatives:
                    return {
                        "model": alternatives[current_model],
                        "reason": "quota_exhausted",
                    }

        elif resource_type == ResourceType.MEMORY:
            # Suggest memory reduction strategies
            return {
                "strategy": "reduce_memory",
                "actions": ["clear_cache", "reduce_batch_size", "disable_features"],
            }

        elif resource_type == ResourceType.DATABASE:
            # Suggest using cache or read replica
            return {"strategy": "use_cache", "fallback": "read_replica"}

        return None

    def record_usage(
        self,
        resource_type: ResourceType,
        amount: float,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Record resource usage for tracking

        Args:
            resource_type: Type of resource used
            amount: Amount used (units depend on resource type)
            context: Additional context
        """
        timestamp = datetime.now().isoformat()

        # Create usage record
        usage_record = {
            "timestamp": timestamp,
            "resource_type": resource_type.value,
            "amount": amount,
            "context": context or {},
        }

        # Save to file
        usage_file = self.storage_path / f"{resource_type.value}_usage.jsonl"
        with open(usage_file, "a") as f:
            f.write(json.dumps(usage_record) + "\n")

    def get_resource_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get resource usage report

        Args:
            hours: Number of hours to include in report

        Returns:
            Resource usage report
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "period_hours": hours,
            "resources": {},
        }

        # Check all resource types
        for resource_type in ResourceType:
            status, usage = self.check_resource(resource_type)
            report["resources"][resource_type.value] = {
                "status": status.value,
                "usage_percentage": usage,
                "healthy": status == ResourceStatus.HEALTHY,
            }

        # Add system info
        report["system"] = {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "disk_usage_percent": psutil.disk_usage("/").percent,
        }

        return report
