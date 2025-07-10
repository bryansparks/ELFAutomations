"""
Smart Chunker Agent
Splits documents into optimal chunks while preserving context and entity boundaries.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import tiktoken
from shared.utils import get_supabase_client

logger = logging.getLogger(__name__)


@dataclass
class RAGChunkConfig:
    """Configuration for chunking strategy"""

    strategy: str
    chunk_size: int = 1000
    overlap: int = 200
    preserve_entities: bool = True
    respect_boundaries: List[str] = None
    min_chunk_size: int = 100
    max_chunk_size: int = 2000


class RAGSmartChunkerAgent:
    """Agent responsible for intelligent document chunking"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.name = "smart_chunker"
        self.role = "Smart Chunker"
        self.backstory = "A structural expert who understands how to segment information meaningfully"

    async def chunk(
        self,
        content: str,
        strategy: Dict[str, Any],
        entities: List[Dict[str, Any]] = None,
        preserve_entities: bool = True,
    ) -> Dict[str, Any]:
        """Chunk document using specified strategy"""
        try:
            # Create chunk configuration
            config = ChunkConfig(
                strategy=strategy.get("primary_strategy", "sliding_window"),
                chunk_size=strategy.get("chunk_size", 1000),
                overlap=strategy.get("overlap", 200),
                preserve_entities=strategy.get("preserve_entities", preserve_entities),
                respect_boundaries=strategy.get("respect_boundaries", []),
            )

            # Choose chunking method
            chunks = []
            if config.strategy == "semantic":
                chunks = await self._semantic_chunking(content, config, entities)
            elif config.strategy == "structural":
                chunks = await self._structural_chunking(content, config)
            elif config.strategy == "entity_aware":
                chunks = await self._entity_aware_chunking(content, config, entities)
            else:  # Default to sliding window
                chunks = await self._sliding_window_chunking(content, config)

            # Create chunk relationships
            relationships = self._create_chunk_relationships(chunks)

            # Add metadata to chunks
            chunks = self._enrich_chunks(chunks, entities)

            logger.info(
                f"Created {len(chunks)} chunks using {config.strategy} strategy"
            )

            return {
                "chunks": chunks,
                "relationships": relationships,
                "metadata": {
                    "strategy": config.strategy,
                    "avg_chunk_size": sum(c["token_count"] for c in chunks)
                    / len(chunks)
                    if chunks
                    else 0,
                    "total_chunks": len(chunks),
                },
            }

        except Exception as e:
            logger.error(f"Chunking error: {str(e)}")
            # Fallback to simple chunking
            return self._fallback_chunking(content)

    async def _sliding_window_chunking(
        self, content: str, config: ChunkConfig
    ) -> List[Dict[str, Any]]:
        """Traditional sliding window chunking with token awareness"""
        chunks = []
        tokens = self.tokenizer.encode(content)

        start = 0
        chunk_index = 0

        while start < len(tokens):
            # Calculate end position
            end = min(start + config.chunk_size, len(tokens))

            # Get chunk tokens
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)

            # Clean up chunk boundaries
            chunk_text = self._clean_chunk_boundaries(chunk_text)

            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": chunk_text,
                    "token_count": len(chunk_tokens),
                    "start_position": start,
                    "end_position": end,
                    "type": "sliding_window",
                }
            )

            # Move to next chunk with overlap
            start = end - config.overlap if end < len(tokens) else end
            chunk_index += 1

        return chunks

    async def _semantic_chunking(
        self, content: str, config: ChunkConfig, entities: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Chunk based on semantic boundaries (paragraphs, sections)"""
        chunks = []
        chunk_index = 0

        # Split by double newlines (paragraphs)
        paragraphs = re.split(r"\n\n+", content)

        current_chunk = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = len(self.tokenizer.encode(para))

            # Check if adding this paragraph exceeds chunk size
            if current_tokens + para_tokens > config.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": chunk_text,
                        "token_count": current_tokens,
                        "type": "semantic",
                    }
                )
                chunk_index += 1

                # Start new chunk with overlap
                if config.overlap > 0 and len(current_chunk) > 1:
                    # Keep last paragraph for overlap
                    current_chunk = [current_chunk[-1], para]
                    current_tokens = len(
                        self.tokenizer.encode("\n\n".join(current_chunk))
                    )
                else:
                    current_chunk = [para]
                    current_tokens = para_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": chunk_text,
                    "token_count": current_tokens,
                    "type": "semantic",
                }
            )

        return chunks

    async def _structural_chunking(
        self, content: str, config: ChunkConfig
    ) -> List[Dict[str, Any]]:
        """Chunk based on document structure (headings, sections)"""
        chunks = []
        chunk_index = 0

        # Patterns for structural elements
        heading_pattern = r"^#+\s+.+$|^.+\n[=-]+$|^[A-Z][A-Z\s]+:$|^\d+\.?\s+[A-Z]"

        # Split content into lines
        lines = content.split("\n")

        current_section = []
        current_tokens = 0
        current_heading = None

        for i, line in enumerate(lines):
            is_heading = bool(re.match(heading_pattern, line, re.MULTILINE))

            if is_heading and current_section:
                # Save current section
                section_text = "\n".join(current_section)
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": section_text,
                        "token_count": current_tokens,
                        "heading": current_heading,
                        "type": "structural",
                    }
                )
                chunk_index += 1

                # Start new section
                current_section = [line]
                current_heading = line.strip()
                current_tokens = len(self.tokenizer.encode(line))
            else:
                # Add to current section
                line_tokens = len(self.tokenizer.encode(line))

                # Check size limit
                if current_tokens + line_tokens > config.chunk_size and current_section:
                    # Save current section
                    section_text = "\n".join(current_section)
                    chunks.append(
                        {
                            "chunk_index": chunk_index,
                            "content": section_text,
                            "token_count": current_tokens,
                            "heading": current_heading,
                            "type": "structural",
                        }
                    )
                    chunk_index += 1

                    # Start new section
                    current_section = [line]
                    current_tokens = line_tokens
                else:
                    current_section.append(line)
                    current_tokens += line_tokens

        # Add final section
        if current_section:
            section_text = "\n".join(current_section)
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": section_text,
                    "token_count": current_tokens,
                    "heading": current_heading,
                    "type": "structural",
                }
            )

        return chunks

    async def _entity_aware_chunking(
        self, content: str, config: ChunkConfig, entities: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Chunk while preserving entity boundaries"""
        if not entities:
            # Fall back to semantic chunking
            return await self._semantic_chunking(content, config, entities)

        chunks = []
        chunk_index = 0

        # Create entity position map
        entity_positions = self._map_entity_positions(content, entities)

        # Sort positions
        sorted_positions = sorted(entity_positions, key=lambda x: x[0])

        current_start = 0
        current_chunk_text = ""
        current_tokens = 0

        for start, end, entity in sorted_positions:
            # Text before entity
            pre_text = content[current_start:start]
            pre_tokens = len(self.tokenizer.encode(pre_text))

            # Entity text
            entity_text = content[start:end]
            entity_tokens = len(self.tokenizer.encode(entity_text))

            # Check if adding would exceed limit
            if (
                current_tokens + pre_tokens + entity_tokens > config.chunk_size
                and current_chunk_text
            ):
                # Save current chunk
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": current_chunk_text.strip(),
                        "token_count": current_tokens,
                        "type": "entity_aware",
                    }
                )
                chunk_index += 1

                # Start new chunk
                current_chunk_text = pre_text + entity_text
                current_tokens = pre_tokens + entity_tokens
            else:
                # Add to current chunk
                current_chunk_text += pre_text + entity_text
                current_tokens += pre_tokens + entity_tokens

            current_start = end

        # Add remaining text
        if current_start < len(content):
            remaining = content[current_start:]
            remaining_tokens = len(self.tokenizer.encode(remaining))

            if (
                current_tokens + remaining_tokens > config.chunk_size
                and current_chunk_text
            ):
                # Save current chunk
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": current_chunk_text.strip(),
                        "token_count": current_tokens,
                        "type": "entity_aware",
                    }
                )
                chunk_index += 1

                # Create final chunk
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": remaining.strip(),
                        "token_count": remaining_tokens,
                        "type": "entity_aware",
                    }
                )
            else:
                current_chunk_text += remaining
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": current_chunk_text.strip(),
                        "token_count": current_tokens + remaining_tokens,
                        "type": "entity_aware",
                    }
                )

        return chunks

    def _map_entity_positions(
        self, content: str, entities: List[Dict[str, Any]]
    ) -> List[Tuple[int, int, Dict]]:
        """Map entity positions in content"""
        positions = []

        for entity in entities:
            source_text = entity.get("source_text", entity.get("value", ""))
            if source_text:
                # Find all occurrences
                start = 0
                while True:
                    pos = content.find(source_text, start)
                    if pos == -1:
                        break
                    positions.append((pos, pos + len(source_text), entity))
                    start = pos + 1

        return positions

    def _clean_chunk_boundaries(self, text: str) -> str:
        """Clean up chunk boundaries to avoid breaking words or sentences"""
        # Remove incomplete sentences at start
        if text and not text[0].isupper() and "." in text[:50]:
            first_sentence = text.find(". ")
            if first_sentence > 0:
                text = text[first_sentence + 2 :]

        # Remove incomplete sentences at end
        if text and text[-1] not in ".!?":
            last_sentence = text.rfind(". ")
            if last_sentence > len(text) - 100:
                text = text[: last_sentence + 1]

        return text.strip()

    def _create_chunk_relationships(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create relationships between chunks"""
        relationships = []

        for i, chunk in enumerate(chunks):
            # Next chunk relationship
            if i < len(chunks) - 1:
                relationships.append(
                    {
                        "source_chunk_index": i,
                        "target_chunk_index": i + 1,
                        "relationship_type": "NEXT_CHUNK",
                    }
                )

            # Previous chunk relationship
            if i > 0:
                relationships.append(
                    {
                        "source_chunk_index": i,
                        "target_chunk_index": i - 1,
                        "relationship_type": "PREVIOUS_CHUNK",
                    }
                )

            # Parent section relationships for structural chunks
            if chunk.get("type") == "structural" and chunk.get("heading"):
                # Find parent sections based on heading hierarchy
                for j in range(i - 1, -1, -1):
                    if chunks[j].get("type") == "structural":
                        if self._is_parent_heading(
                            chunks[j].get("heading", ""), chunk.get("heading", "")
                        ):
                            relationships.append(
                                {
                                    "source_chunk_index": i,
                                    "target_chunk_index": j,
                                    "relationship_type": "PARENT_SECTION",
                                }
                            )
                            break

        return relationships

    def _is_parent_heading(self, potential_parent: str, child: str) -> bool:
        """Determine if one heading is parent of another"""
        # Simple heuristic based on heading levels
        parent_level = (
            len(re.match(r"^#+", potential_parent).group())
            if re.match(r"^#+", potential_parent)
            else 0
        )
        child_level = (
            len(re.match(r"^#+", child).group()) if re.match(r"^#+", child) else 0
        )

        return parent_level > 0 and child_level > parent_level

    def _enrich_chunks(
        self, chunks: List[Dict[str, Any]], entities: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Add metadata to chunks"""
        enriched = []

        for chunk in chunks:
            # Add entities found in chunk
            chunk_entities = []
            if entities:
                for entity in entities:
                    if (
                        entity.get("value", "") in chunk["content"]
                        or entity.get("source_text", "") in chunk["content"]
                    ):
                        chunk_entities.append(
                            {"type": entity["type"], "value": entity["value"]}
                        )

            chunk["entities"] = chunk_entities
            chunk["entity_count"] = len(chunk_entities)

            # Add additional metadata
            chunk["word_count"] = len(chunk["content"].split())
            chunk["char_count"] = len(chunk["content"])

            enriched.append(chunk)

        return enriched

    def _fallback_chunking(self, content: str) -> Dict[str, Any]:
        """Simple fallback chunking if advanced methods fail"""
        chunks = []
        chunk_size = 1000

        words = content.split()
        current_chunk = []

        for i, word in enumerate(words):
            current_chunk.append(word)

            if len(" ".join(current_chunk)) > chunk_size:
                chunk_text = " ".join(current_chunk[:-1])
                chunks.append(
                    {
                        "chunk_index": len(chunks),
                        "content": chunk_text,
                        "token_count": len(self.tokenizer.encode(chunk_text)),
                        "type": "fallback",
                    }
                )
                current_chunk = [word]

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "content": chunk_text,
                    "token_count": len(self.tokenizer.encode(chunk_text)),
                    "type": "fallback",
                }
            )

        return {
            "chunks": chunks,
            "relationships": [],
            "metadata": {"strategy": "fallback"},
        }

    async def chunk_document(self, *args, **kwargs):
        """Alias for chunk method"""
        return await self.chunk(*args, **kwargs)

    async def create_chunk_relationships(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create relationships between chunks"""
        return self._create_chunk_relationships(chunks)

    async def validate_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate chunk quality"""
        issues = []

        for chunk in chunks:
            # Check size
            if chunk["token_count"] < 50:
                issues.append(
                    f"Chunk {chunk['chunk_index']} too small ({chunk['token_count']} tokens)"
                )
            elif chunk["token_count"] > 2000:
                issues.append(
                    f"Chunk {chunk['chunk_index']} too large ({chunk['token_count']} tokens)"
                )

            # Check content
            if not chunk["content"].strip():
                issues.append(f"Chunk {chunk['chunk_index']} is empty")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "total_chunks": len(chunks),
        }
