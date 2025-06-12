"""Mock Qdrant client for development without Qdrant server."""

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MockPoint:
    """Mock representation of a Qdrant point."""

    id: str
    vector: List[float]
    payload: Dict[str, Any]
    score: float = 1.0


@dataclass
class MockFilter:
    """Mock filter for search operations."""

    must: List[Dict[str, Any]] = None
    should: List[Dict[str, Any]] = None
    must_not: List[Dict[str, Any]] = None


class MockQdrantClient:
    """Mock Qdrant client that stores vectors in memory.

    This allows development and testing of the Memory & Learning System
    without requiring a running Qdrant instance.
    """

    def __init__(self, host: str = "mock", port: int = 6333):
        """Initialize mock client."""
        self.host = host
        self.port = port
        self.collections = {}
        logger.info(f"[MOCK QDRANT] Initialized mock client at {host}:{port}")

    def create_collection(self, collection_name: str, vectors_config: Any = None):
        """Create a mock collection."""
        if collection_name in self.collections:
            logger.warning(f"[MOCK QDRANT] Collection {collection_name} already exists")
            return

        self.collections[collection_name] = {
            "config": vectors_config,
            "points": {},
            "next_id": 1,
        }
        logger.info(f"[MOCK QDRANT] Created collection: {collection_name}")

    def delete_collection(self, collection_name: str):
        """Delete a mock collection."""
        if collection_name in self.collections:
            del self.collections[collection_name]
            logger.info(f"[MOCK QDRANT] Deleted collection: {collection_name}")

    def get_collections(self):
        """List all collections."""
        collections = [{"name": name} for name in self.collections.keys()]
        logger.info(f"[MOCK QDRANT] Listing {len(collections)} collections")
        return type("obj", (object,), {"collections": collections})

    def get_collection(self, collection_name: str):
        """Get collection info."""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")

        collection = self.collections[collection_name]
        points_count = len(collection["points"])

        # Return mock collection info
        return type(
            "obj",
            (object,),
            {
                "points_count": points_count,
                "config": type(
                    "obj",
                    (object,),
                    {
                        "params": type(
                            "obj",
                            (object,),
                            {
                                "vectors": type(
                                    "obj",
                                    (object,),
                                    {
                                        "size": collection["config"].size
                                        if collection["config"]
                                        else 384,
                                        "distance": "Cosine",
                                    },
                                )
                            },
                        )
                    },
                ),
            },
        )

    def upsert(self, collection_name: str, points: List[Any]):
        """Insert or update points in collection."""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")

        collection = self.collections[collection_name]

        for point in points:
            # Handle both dict and object inputs
            if hasattr(point, "id"):
                point_id = point.id
                vector = point.vector
                payload = point.payload
            else:
                point_id = point.get("id", str(uuid.uuid4()))
                vector = point.get("vector", [])
                payload = point.get("payload", {})

            # Store the point
            collection["points"][point_id] = MockPoint(
                id=point_id, vector=vector, payload=payload
            )

        logger.info(
            f"[MOCK QDRANT] Upserted {len(points)} points into {collection_name}"
        )

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_filter: Optional[Any] = None,
        limit: int = 5,
    ):
        """Mock similarity search."""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")

        collection = self.collections[collection_name]
        all_points = list(collection["points"].values())

        # Apply filters if provided
        if query_filter:
            filtered_points = self._apply_filter(all_points, query_filter)
        else:
            filtered_points = all_points

        # Mock similarity scoring (random for now)
        results = []
        for i, point in enumerate(filtered_points[:limit]):
            # Simple mock scoring - in real Qdrant this would be cosine similarity
            score = 1.0 - (i * 0.1)  # Decreasing scores
            point.score = max(0.0, score)
            results.append(point)

        logger.info(
            f"[MOCK QDRANT] Searched {collection_name}, returning {len(results)} results"
        )
        return results

    def retrieve(self, collection_name: str, ids: List[str]):
        """Retrieve points by IDs."""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")

        collection = self.collections[collection_name]
        results = []

        for point_id in ids:
            if point_id in collection["points"]:
                results.append(collection["points"][point_id])

        return results

    def count(self, collection_name: str, exact: bool = True):
        """Count points in collection."""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")

        count = len(self.collections[collection_name]["points"])
        return type("obj", (object,), {"count": count})

    def _apply_filter(
        self, points: List[MockPoint], query_filter: Any
    ) -> List[MockPoint]:
        """Apply basic filtering to points."""
        filtered = []

        # Simple filter implementation - just check exact matches
        for point in points:
            include = True

            # Check must conditions
            if hasattr(query_filter, "must") and query_filter.must:
                for condition in query_filter.must:
                    if hasattr(condition, "key") and hasattr(condition, "match"):
                        key = condition.key
                        expected_value = (
                            condition.match.value
                            if hasattr(condition.match, "value")
                            else condition.match
                        )

                        if (
                            key not in point.payload
                            or point.payload[key] != expected_value
                        ):
                            include = False
                            break

            if include:
                filtered.append(point)

        return filtered

    # Compatibility methods for common patterns
    def recreate_collection(self, collection_name: str, vectors_config: Any = None):
        """Recreate collection (delete if exists, then create)."""
        if collection_name in self.collections:
            self.delete_collection(collection_name)
        self.create_collection(collection_name, vectors_config)

    def update_collection(self, collection_name: str, optimizer_config: Any = None):
        """Mock collection update."""
        logger.info(f"[MOCK QDRANT] Updated collection {collection_name} config")


# Convenience function for development
def get_qdrant_client(use_mock: bool = True, **kwargs) -> Any:
    """Get either mock or real Qdrant client based on environment.

    Args:
        use_mock: If True, return MockQdrantClient. If False, attempt to import real client.
        **kwargs: Arguments passed to client constructor

    Returns:
        Either MockQdrantClient or real QdrantClient
    """
    if use_mock:
        return MockQdrantClient(**kwargs)
    else:
        try:
            from qdrant_client import QdrantClient

            return QdrantClient(**kwargs)
        except ImportError:
            logger.warning("qdrant_client not installed, using mock")
            return MockQdrantClient(**kwargs)
