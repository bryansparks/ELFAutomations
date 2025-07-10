"""
RAG Health Monitor
Monitors the health and performance of the RAG system components.

Features:
- Qdrant connectivity and performance monitoring
- Neo4j connectivity and query performance
- Supabase queue and storage monitoring
- Embedding generation latency tracking
- Alert generation for issues
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from ..config import settings
from ..utils import get_supabase_client

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status for a component"""

    name: str
    status: HealthStatus
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = None
    last_check: datetime = None

    def __post_init__(self):
        if self.last_check is None:
            self.last_check = datetime.utcnow()
        if self.metrics is None:
            self.metrics = {}


@dataclass
class Alert:
    """System alert"""

    component: str
    severity: str  # info, warning, critical
    message: str
    timestamp: datetime = None
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}


class RAGHealthMonitor:
    """Monitor health of RAG system components"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.qdrant_client = None
        self.neo4j_driver = None

        # Configuration
        self.qdrant_url = settings.get("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = settings.get("QDRANT_API_KEY")
        self.neo4j_uri = settings.get("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = settings.get("NEO4J_USER", "neo4j")
        self.neo4j_password = settings.get("NEO4J_PASSWORD")

        # Health history
        self.health_history: List[Dict[str, ComponentHealth]] = []
        self.alerts: List[Alert] = []

        # Thresholds
        self.latency_thresholds = {
            "qdrant": {"warning": 100, "critical": 500},
            "neo4j": {"warning": 200, "critical": 1000},
            "supabase": {"warning": 150, "critical": 750},
            "embedding": {"warning": 1000, "critical": 5000},
        }

        self.queue_thresholds = {
            "backlog": {"warning": 50, "critical": 200},
            "failed_rate": {"warning": 0.1, "critical": 0.25},
            "processing_time": {"warning": 300, "critical": 600},
        }

    async def initialize(self):
        """Initialize connections"""
        try:
            # Initialize Qdrant
            self.qdrant_client = QdrantClient(
                url=self.qdrant_url, api_key=self.qdrant_api_key
            )

            # Initialize Neo4j
            if self.neo4j_uri and self.neo4j_password:
                self.neo4j_driver = GraphDatabase.driver(
                    self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
                )
        except Exception as e:
            logger.error(f"Failed to initialize connections: {str(e)}")

    async def check_qdrant_health(self) -> ComponentHealth:
        """Check Qdrant health and performance"""
        start_time = time.time()

        try:
            if not self.qdrant_client:
                await self.initialize()

            # Check collections exist
            collections = await self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]

            required_collections = ["document_embeddings", "entity_embeddings"]
            missing = [c for c in required_collections if c not in collection_names]

            if missing:
                return ComponentHealth(
                    name="qdrant",
                    status=HealthStatus.WARNING,
                    error=f"Missing collections: {', '.join(missing)}",
                    metrics={"collections": len(collection_names)},
                )

            # Test search performance
            test_vector = [0.0] * 3072  # Dummy vector
            search_start = time.time()

            result = await self.qdrant_client.search(
                collection_name="document_embeddings", query_vector=test_vector, limit=1
            )

            search_latency = (time.time() - search_start) * 1000

            # Get collection stats
            stats = {}
            for collection in required_collections:
                try:
                    info = await self.qdrant_client.get_collection(collection)
                    stats[collection] = {
                        "vectors_count": info.vectors_count,
                        "indexed_vectors_count": info.indexed_vectors_count,
                    }
                except:
                    pass

            latency = (time.time() - start_time) * 1000

            # Determine status
            status = HealthStatus.HEALTHY
            if latency > self.latency_thresholds["qdrant"]["critical"]:
                status = HealthStatus.CRITICAL
            elif latency > self.latency_thresholds["qdrant"]["warning"]:
                status = HealthStatus.WARNING

            return ComponentHealth(
                name="qdrant",
                status=status,
                latency_ms=latency,
                metrics={
                    "collections": len(collection_names),
                    "search_latency_ms": search_latency,
                    "collection_stats": stats,
                },
            )

        except Exception as e:
            return ComponentHealth(
                name="qdrant",
                status=HealthStatus.CRITICAL,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def check_neo4j_health(self) -> ComponentHealth:
        """Check Neo4j health and performance"""
        start_time = time.time()

        try:
            if not self.neo4j_driver:
                await self.initialize()

            if not self.neo4j_driver:
                return ComponentHealth(
                    name="neo4j",
                    status=HealthStatus.UNKNOWN,
                    error="Neo4j not configured",
                )

            # Test connection and basic query
            with self.neo4j_driver.session() as session:
                # Count nodes
                query_start = time.time()
                result = session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
                node_count = result.single()["count"]
                query_latency = (time.time() - query_start) * 1000

                # Count relationships
                result = session.run(
                    "MATCH ()-[r]->() RETURN count(r) as count LIMIT 1"
                )
                relationship_count = result.single()["count"]

                # Get label distribution
                result = session.run(
                    """
                    MATCH (n)
                    RETURN labels(n)[0] as label, count(n) as count
                    ORDER BY count DESC
                    LIMIT 10
                """
                )
                label_distribution = {
                    record["label"]: record["count"] for record in result
                }

            latency = (time.time() - start_time) * 1000

            # Determine status
            status = HealthStatus.HEALTHY
            if latency > self.latency_thresholds["neo4j"]["critical"]:
                status = HealthStatus.CRITICAL
            elif latency > self.latency_thresholds["neo4j"]["warning"]:
                status = HealthStatus.WARNING

            return ComponentHealth(
                name="neo4j",
                status=status,
                latency_ms=latency,
                metrics={
                    "node_count": node_count,
                    "relationship_count": relationship_count,
                    "query_latency_ms": query_latency,
                    "label_distribution": label_distribution,
                },
            )

        except Exception as e:
            return ComponentHealth(
                name="neo4j",
                status=HealthStatus.CRITICAL,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def check_supabase_health(self) -> ComponentHealth:
        """Check Supabase health and queue status"""
        start_time = time.time()

        try:
            # Test connection
            query_start = time.time()
            result = (
                self.supabase.table("rag_documents").select("id").limit(1).execute()
            )
            query_latency = (time.time() - query_start) * 1000

            # Get queue statistics
            queue_stats = await self._get_queue_statistics()

            # Get storage statistics
            storage_stats = await self._get_storage_statistics()

            latency = (time.time() - start_time) * 1000

            # Determine status based on queue health
            status = HealthStatus.HEALTHY

            if queue_stats["backlog"] > self.queue_thresholds["backlog"]["critical"]:
                status = HealthStatus.CRITICAL
            elif queue_stats["backlog"] > self.queue_thresholds["backlog"]["warning"]:
                status = HealthStatus.WARNING

            if (
                queue_stats["failed_rate"]
                > self.queue_thresholds["failed_rate"]["critical"]
            ):
                status = HealthStatus.CRITICAL
            elif (
                queue_stats["failed_rate"]
                > self.queue_thresholds["failed_rate"]["warning"]
            ):
                status = HealthStatus.WARNING

            return ComponentHealth(
                name="supabase",
                status=status,
                latency_ms=latency,
                metrics={
                    "query_latency_ms": query_latency,
                    "queue": queue_stats,
                    "storage": storage_stats,
                },
            )

        except Exception as e:
            return ComponentHealth(
                name="supabase",
                status=HealthStatus.CRITICAL,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def check_embedding_performance(self) -> ComponentHealth:
        """Check embedding generation performance"""
        start_time = time.time()

        try:
            # Get recent embedding generation times
            window_start = datetime.utcnow() - timedelta(hours=1)

            result = (
                self.supabase.table("rag_extraction_history")
                .select("extraction_time_ms")
                .eq("extraction_type", "embeddings")
                .eq("status", "completed")
                .gte("created_at", window_start.isoformat())
                .execute()
            )

            if not result.data:
                return ComponentHealth(
                    name="embedding",
                    status=HealthStatus.UNKNOWN,
                    error="No recent embedding data",
                )

            # Calculate statistics
            times = [
                r["extraction_time_ms"]
                for r in result.data
                if r.get("extraction_time_ms")
            ]

            if not times:
                return ComponentHealth(
                    name="embedding",
                    status=HealthStatus.UNKNOWN,
                    error="No timing data available",
                )

            avg_time = np.mean(times)
            p95_time = np.percentile(times, 95)

            # Determine status
            status = HealthStatus.HEALTHY
            if p95_time > self.latency_thresholds["embedding"]["critical"]:
                status = HealthStatus.CRITICAL
            elif p95_time > self.latency_thresholds["embedding"]["warning"]:
                status = HealthStatus.WARNING

            return ComponentHealth(
                name="embedding",
                status=status,
                metrics={
                    "avg_generation_time_ms": avg_time,
                    "p95_generation_time_ms": p95_time,
                    "samples": len(times),
                },
            )

        except Exception as e:
            return ComponentHealth(
                name="embedding",
                status=HealthStatus.CRITICAL,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def _get_queue_statistics(self) -> Dict[str, Any]:
        """Get processing queue statistics"""
        try:
            # Count by status
            pending = (
                self.supabase.table("rag_processing_queue")
                .select("id", count="exact")
                .eq("status", "pending")
                .execute()
            )

            processing = (
                self.supabase.table("rag_processing_queue")
                .select("id", count="exact")
                .eq("status", "processing")
                .execute()
            )

            failed = (
                self.supabase.table("rag_processing_queue")
                .select("id", count="exact")
                .eq("status", "failed")
                .execute()
            )

            # Get processing times for completed items
            window_start = datetime.utcnow() - timedelta(hours=1)

            completed = (
                self.supabase.table("rag_processing_queue")
                .select("started_at, completed_at")
                .eq("status", "completed")
                .gte("completed_at", window_start.isoformat())
                .execute()
            )

            processing_times = []
            if completed.data:
                for item in completed.data:
                    if item.get("started_at") and item.get("completed_at"):
                        start = datetime.fromisoformat(
                            item["started_at"].replace("Z", "+00:00")
                        )
                        end = datetime.fromisoformat(
                            item["completed_at"].replace("Z", "+00:00")
                        )
                        processing_times.append((end - start).total_seconds())

            total = pending.count + processing.count + failed.count
            failed_rate = failed.count / total if total > 0 else 0

            return {
                "pending": pending.count,
                "processing": processing.count,
                "failed": failed.count,
                "backlog": pending.count,
                "failed_rate": failed_rate,
                "avg_processing_time": np.mean(processing_times)
                if processing_times
                else 0,
                "p95_processing_time": np.percentile(processing_times, 95)
                if processing_times
                else 0,
            }

        except Exception as e:
            logger.error(f"Error getting queue statistics: {str(e)}")
            return {}

    async def _get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage utilization statistics"""
        try:
            # Document count and size
            docs = (
                self.supabase.table("rag_documents")
                .select("size_bytes")
                .eq("status", "completed")
                .execute()
            )

            total_size = sum(d.get("size_bytes", 0) for d in (docs.data or []))

            # Chunks count
            chunks = (
                self.supabase.table("rag_document_chunks")
                .select("id", count="exact")
                .execute()
            )

            # Entities count
            entities = (
                self.supabase.table("rag_extracted_entities")
                .select("id", count="exact")
                .execute()
            )

            return {
                "documents": len(docs.data) if docs.data else 0,
                "total_size_gb": total_size / (1024**3),
                "chunks": chunks.count,
                "entities": entities.count,
            }

        except Exception as e:
            logger.error(f"Error getting storage statistics: {str(e)}")
            return {}

    def generate_alerts(self, health_status: Dict[str, ComponentHealth]) -> List[Alert]:
        """Generate alerts based on health status"""
        alerts = []

        for component_name, health in health_status.items():
            if health.status == HealthStatus.CRITICAL:
                alerts.append(
                    Alert(
                        component=component_name,
                        severity="critical",
                        message=f"{component_name} is in critical state: {health.error or 'High latency'}",
                        details=health.metrics,
                    )
                )
            elif health.status == HealthStatus.WARNING:
                alerts.append(
                    Alert(
                        component=component_name,
                        severity="warning",
                        message=f"{component_name} performance degraded",
                        details=health.metrics,
                    )
                )

        # Check for specific conditions
        supabase_health = health_status.get("supabase")
        if supabase_health and supabase_health.metrics:
            queue = supabase_health.metrics.get("queue", {})

            if queue.get("backlog", 0) > self.queue_thresholds["backlog"]["critical"]:
                alerts.append(
                    Alert(
                        component="queue",
                        severity="critical",
                        message=f"Queue backlog critical: {queue['backlog']} documents pending",
                        details=queue,
                    )
                )

            if (
                queue.get("failed_rate", 0)
                > self.queue_thresholds["failed_rate"]["warning"]
            ):
                alerts.append(
                    Alert(
                        component="queue",
                        severity="warning",
                        message=f"High failure rate: {queue['failed_rate']:.1%}",
                        details=queue,
                    )
                )

        return alerts

    async def check_all_components(
        self,
    ) -> Tuple[Dict[str, ComponentHealth], List[Alert]]:
        """Check health of all components"""
        health_status = {}

        # Check each component
        health_status["qdrant"] = await self.check_qdrant_health()
        health_status["neo4j"] = await self.check_neo4j_health()
        health_status["supabase"] = await self.check_supabase_health()
        health_status["embedding"] = await self.check_embedding_performance()

        # Generate alerts
        alerts = self.generate_alerts(health_status)

        # Store in history
        self.health_history.append(
            {"timestamp": datetime.utcnow(), "health": health_status}
        )

        # Keep only last hour of history
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self.health_history = [
            h for h in self.health_history if h["timestamp"] > cutoff
        ]

        # Add new alerts
        self.alerts.extend(alerts)

        return health_status, alerts

    async def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        health_status, alerts = await self.check_all_components()

        # Calculate overall status
        statuses = [h.status for h in health_status.values()]

        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
        elif HealthStatus.UNKNOWN in statuses:
            overall_status = HealthStatus.UNKNOWN
        else:
            overall_status = HealthStatus.HEALTHY

        return {
            "overall_status": overall_status.value,
            "components": {
                name: {
                    "status": health.status.value,
                    "latency_ms": health.latency_ms,
                    "error": health.error,
                    "metrics": health.metrics,
                }
                for name, health in health_status.items()
            },
            "alerts": [
                {
                    "component": alert.component,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in alerts
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def monitor_continuously(self, interval: int = 60, callback=None):
        """Monitor health continuously"""
        logger.info(f"Starting continuous health monitoring (interval: {interval}s)")

        while True:
            try:
                summary = await self.get_health_summary()

                if callback:
                    await callback(summary)

                # Log critical alerts
                for alert in self.alerts:
                    if alert.severity == "critical":
                        logger.error(f"CRITICAL: {alert.component} - {alert.message}")

                # Clear processed alerts
                self.alerts = []

            except Exception as e:
                logger.error(f"Error in health monitoring: {str(e)}")

            await asyncio.sleep(interval)

    async def cleanup(self):
        """Cleanup connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
