"""
Embedding Generator Agent
Generates high-quality embeddings for document chunks using OpenAI's embedding models.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import openai
from shared.utils import get_supabase_client
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class RAGEmbeddingGeneratorAgent:
    """Agent responsible for generating embeddings from text chunks"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.name = "embedding_generator"
        self.role = "Embedding Generator"
        self.backstory = "A semantic specialist who captures meaning in vector space"

        # Embedding models and dimensions
        self.model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

        # Default model
        self.default_model = "text-embedding-3-large"

    async def generate(
        self, chunks: List[Dict[str, Any]], model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate embeddings for chunks"""
        try:
            model = model or self.default_model

            if model not in self.model_dimensions:
                logger.warning(f"Unknown model {model}, using default")
                model = self.default_model

            # Process chunks in batches
            embeddings = await self._generate_embeddings_batch(chunks, model)

            # Add metadata to embeddings
            enriched_embeddings = self._enrich_embeddings(embeddings, chunks, model)

            logger.info(
                f"Generated {len(enriched_embeddings)} embeddings using {model}"
            )

            return {
                "embeddings": enriched_embeddings,
                "model": model,
                "dimension": self.model_dimensions[model],
                "metadata": {
                    "total_chunks": len(chunks),
                    "successful_embeddings": len(enriched_embeddings),
                    "model_used": model,
                },
            }

        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _generate_embeddings_batch(
        self, chunks: List[Dict[str, Any]], model: str
    ) -> List[Dict[str, Any]]:
        """Generate embeddings with retry logic"""
        embeddings = []
        batch_size = 20  # OpenAI recommends batches of 20 or fewer

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [chunk["content"] for chunk in batch]

            try:
                # Call OpenAI API
                response = await self._call_openai_embeddings(texts, model)

                # Process response
                for j, embedding_data in enumerate(response.data):
                    embeddings.append(
                        {
                            "chunk_index": batch[j]["chunk_index"],
                            "embedding": embedding_data.embedding,
                            "index": embedding_data.index,
                        }
                    )

            except openai.RateLimitError:
                logger.warning("Rate limit hit, waiting before retry")
                await asyncio.sleep(20)
                raise
            except Exception as e:
                logger.error(f"Error in batch {i//batch_size}: {str(e)}")
                # Continue with next batch instead of failing entirely
                for j, chunk in enumerate(batch):
                    embeddings.append(
                        {
                            "chunk_index": chunk["chunk_index"],
                            "embedding": None,
                            "error": str(e),
                        }
                    )

        return embeddings

    async def _call_openai_embeddings(self, texts: List[str], model: str):
        """Call OpenAI embeddings API"""
        client = openai.AsyncOpenAI()

        # Clean texts
        cleaned_texts = [self._clean_text_for_embedding(text) for text in texts]

        response = await client.embeddings.create(input=cleaned_texts, model=model)

        return response

    def _clean_text_for_embedding(self, text: str) -> str:
        """Clean text for embedding generation"""
        # Remove excessive whitespace
        text = " ".join(text.split())

        # Truncate if too long (8191 token limit for embeddings)
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        return text

    def _enrich_embeddings(
        self, embeddings: List[Dict[str, Any]], chunks: List[Dict[str, Any]], model: str
    ) -> List[Dict[str, Any]]:
        """Add metadata to embeddings"""
        enriched = []

        # Create chunk lookup
        chunk_lookup = {chunk["chunk_index"]: chunk for chunk in chunks}

        for embedding_data in embeddings:
            chunk_index = embedding_data["chunk_index"]
            chunk = chunk_lookup.get(chunk_index, {})

            # Skip if embedding failed
            if embedding_data.get("error") or embedding_data.get("embedding") is None:
                logger.warning(f"Skipping failed embedding for chunk {chunk_index}")
                continue

            enriched_embedding = {
                "chunk_index": chunk_index,
                "embedding": embedding_data["embedding"],
                "model": model,
                "dimension": self.model_dimensions[model],
                "metadata": {
                    "chunk_type": chunk.get("type", "unknown"),
                    "token_count": chunk.get("token_count", 0),
                    "entity_count": chunk.get("entity_count", 0),
                    "entities": chunk.get("entities", []),
                    "heading": chunk.get("heading"),
                    "generated_at": datetime.now().isoformat(),
                },
            }

            enriched.append(enriched_embedding)

        return enriched

    async def generate_entity_embeddings(
        self, entities: List[Dict[str, Any]], model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate embeddings for entities"""
        model = model or self.default_model

        # Create pseudo-chunks from entities
        entity_chunks = []
        for i, entity in enumerate(entities):
            # Create rich text representation of entity
            entity_text = self._create_entity_text(entity)
            entity_chunks.append(
                {"chunk_index": f"entity_{i}", "content": entity_text, "entity": entity}
            )

        # Generate embeddings
        result = await self.generate(entity_chunks, model)

        # Map back to entities
        entity_embeddings = []
        for embedding in result["embeddings"]:
            if embedding["chunk_index"].startswith("entity_"):
                idx = int(embedding["chunk_index"].split("_")[1])
                entity_embeddings.append(
                    {
                        "entity": entities[idx],
                        "embedding": embedding["embedding"],
                        "model": model,
                    }
                )

        return {
            "entity_embeddings": entity_embeddings,
            "model": model,
            "total": len(entity_embeddings),
        }

    def _create_entity_text(self, entity: Dict[str, Any]) -> str:
        """Create text representation of entity for embedding"""
        parts = [f"{entity['type']}: {entity['value']}"]

        # Add properties
        if entity.get("properties"):
            for key, value in entity["properties"].items():
                parts.append(f"{key}: {value}")

        # Add context if available
        if entity.get("context"):
            parts.append(f"Context: {entity['context']}")

        return " | ".join(parts)

    async def generate_query_embedding(
        self, query: str, model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding for a search query"""
        model = model or self.default_model

        try:
            response = await self._call_openai_embeddings([query], model)

            if response.data:
                return response.data[0].embedding

        except Exception as e:
            logger.error(f"Query embedding error: {str(e)}")
            raise

        return []

    async def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between embeddings"""
        import numpy as np

        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        return float(similarity)

    async def generate_embeddings(self, *args, **kwargs):
        """Alias for generate method"""
        return await self.generate(*args, **kwargs)

    async def store_vectors(
        self, embeddings: List[Dict[str, Any]], document_id: str, tenant_id: str
    ) -> None:
        """Store embedding metadata in Supabase"""
        try:
            for embedding in embeddings:
                # Store metadata (actual vectors go to Qdrant)
                self.supabase.table("rag_embeddings").insert(
                    {
                        "document_id": document_id,
                        "tenant_id": tenant_id,
                        "chunk_index": embedding["chunk_index"],
                        "model": embedding["model"],
                        "dimension": embedding["dimension"],
                        "metadata": embedding.get("metadata", {}),
                        "created_at": datetime.now().isoformat(),
                    }
                ).execute()

            logger.info(f"Stored metadata for {len(embeddings)} embeddings")

        except Exception as e:
            logger.error(f"Error storing embedding metadata: {str(e)}")
            raise

    async def update_embedding_metadata(
        self, embedding_id: str, metadata: Dict[str, Any]
    ) -> None:
        """Update embedding metadata"""
        try:
            self.supabase.table("rag_embeddings").update(
                {"metadata": metadata, "updated_at": datetime.now().isoformat()}
            ).eq("id", embedding_id).execute()

        except Exception as e:
            logger.error(f"Error updating embedding metadata: {str(e)}")
            raise
