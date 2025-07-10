"""
RAG Processor Team - Main Entry Point
This team processes documents through extraction, chunking, and embedding pipeline.
"""

import asyncio
import logging
import os
from datetime import datetime

from workflows.document_pipeline import process_document_queue

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def health_check():
    """Health check endpoint for Kubernetes"""
    # Check critical dependencies
    checks = {"supabase": False, "openai": False, "neo4j": False, "qdrant": False}

    try:
        # Check Supabase
        from shared.utils import get_supabase_client

        supabase = get_supabase_client()
        result = supabase.table("rag_processing_queue").select("id").limit(1).execute()
        checks["supabase"] = True
    except Exception as e:
        logger.error(f"Supabase health check failed: {str(e)}")

    try:
        # Check OpenAI
        import openai

        client = openai.Client()
        # Just verify client creation
        checks["openai"] = True
    except Exception as e:
        logger.error(f"OpenAI health check failed: {str(e)}")

    try:
        # Check Neo4j
        neo4j_uri = os.getenv("NEO4J_URI")
        checks["neo4j"] = bool(neo4j_uri)
    except Exception as e:
        logger.error(f"Neo4j health check failed: {str(e)}")

    try:
        # Check Qdrant
        qdrant_url = os.getenv("QDRANT_URL")
        checks["qdrant"] = bool(qdrant_url)
    except Exception as e:
        logger.error(f"Qdrant health check failed: {str(e)}")

    all_healthy = all(checks.values())

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
    }


async def main():
    """Main entry point for RAG processor team"""
    logger.info("Starting RAG Processor Team")

    # Perform health check
    health = await health_check()
    logger.info(f"Health check: {health}")

    if health["status"] != "healthy":
        logger.error("Some dependencies are unhealthy, but continuing...")

    # Start processing queue
    try:
        await process_document_queue()
    except KeyboardInterrupt:
        logger.info("Shutting down RAG processor team")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
