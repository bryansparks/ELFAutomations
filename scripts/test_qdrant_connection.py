#!/usr/bin/env python3
"""Test script to verify Qdrant connection and basic operations."""

import os
import sys
import uuid
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from elf_automations.shared.utils.logging import get_logger

logger = get_logger(__name__)


def test_qdrant_connection(host: str = "localhost", port: int = 6333):
    """Test connection to Qdrant and perform basic operations."""
    logger.info(f"Testing Qdrant connection at {host}:{port}")

    try:
        # Initialize client
        client = QdrantClient(host=host, port=port)

        # Test 1: Check if Qdrant is alive
        logger.info("Test 1: Checking Qdrant health...")
        info = client.get_collections()
        logger.info(f"✓ Qdrant is running! Found {len(info.collections)} collections")

        # Test 2: Create a test collection
        collection_name = "test_memory_collection"
        vector_size = 384  # Using smaller vectors for testing

        logger.info(f"\nTest 2: Creating test collection '{collection_name}'...")

        # Delete if exists
        try:
            client.delete_collection(collection_name)
            logger.info("Deleted existing test collection")
        except:
            pass

        # Create collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info("✓ Collection created successfully")

        # Test 3: Insert test vectors
        logger.info("\nTest 3: Inserting test memory vectors...")

        test_memories = [
            {
                "id": str(uuid.uuid4()),
                "vector": np.random.rand(vector_size).tolist(),
                "payload": {
                    "team": "marketing-team",
                    "type": "campaign_outcome",
                    "content": "Social media campaign achieved 250% ROI",
                    "tags": ["marketing", "social_media", "success"],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "vector": np.random.rand(vector_size).tolist(),
                "payload": {
                    "team": "engineering-team",
                    "type": "bug_fix",
                    "content": "Fixed memory leak in async handlers",
                    "tags": ["engineering", "bug_fix", "performance"],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "vector": np.random.rand(vector_size).tolist(),
                "payload": {
                    "team": "sales-team",
                    "type": "customer_insight",
                    "content": "Enterprise customers prefer annual contracts",
                    "tags": ["sales", "customer", "insight"],
                },
            },
        ]

        points = [
            PointStruct(id=mem["id"], vector=mem["vector"], payload=mem["payload"])
            for mem in test_memories
        ]

        client.upsert(collection_name=collection_name, points=points)
        logger.info(f"✓ Inserted {len(points)} test memories")

        # Test 4: Search vectors
        logger.info("\nTest 4: Searching for similar memories...")

        # Create a query vector
        query_vector = np.random.rand(vector_size).tolist()

        search_result = client.search(
            collection_name=collection_name, query_vector=query_vector, limit=2
        )

        logger.info(f"✓ Found {len(search_result)} similar memories:")
        for i, result in enumerate(search_result):
            logger.info(
                f"  {i+1}. Score: {result.score:.3f}, Team: {result.payload['team']}"
            )
            logger.info(f"     Content: {result.payload['content']}")

        # Test 5: Filter search
        logger.info("\nTest 5: Searching with filters...")

        filtered_result = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(key="team", match=MatchValue(value="marketing-team"))
                ]
            ),
            limit=1,
        )

        if filtered_result:
            logger.info(f"✓ Found {len(filtered_result)} marketing team memories")
        else:
            logger.info("No marketing team memories found")

        # Test 6: Get collection info
        logger.info("\nTest 6: Getting collection info...")
        collection_info = client.get_collection(collection_name)
        logger.info(f"✓ Collection '{collection_name}':")
        logger.info(f"  - Vectors count: {collection_info.points_count}")
        logger.info(f"  - Vector size: {collection_info.config.params.vectors.size}")
        logger.info(
            f"  - Distance metric: {collection_info.config.params.vectors.distance}"
        )

        # Cleanup
        logger.info("\nCleaning up...")
        client.delete_collection(collection_name)
        logger.info("✓ Test collection deleted")

        logger.info("\n🎉 All Qdrant tests passed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Qdrant test failed: {e}")
        logger.info("\nMake sure Qdrant is running and accessible:")
        logger.info("  kubectl port-forward -n elf-automations svc/qdrant 6333:6333")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Qdrant connection")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")

    args = parser.parse_args()

    success = test_qdrant_connection(args.host, args.port)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
