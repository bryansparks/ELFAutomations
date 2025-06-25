"""
RAG Processor Team Agents
Each agent handles a specific aspect of the document processing pipeline.
"""

from .document_classifier import DocumentClassifierAgent
from .embedding_generator import EmbeddingGeneratorAgent
from .entity_extractor import EntityExtractorAgent
from .graph_builder import GraphBuilderAgent
from .queue_monitor import QueueMonitorAgent
from .smart_chunker import SmartChunkerAgent
from .storage_coordinator import StorageCoordinatorAgent

# Agent instances
queue_monitor = QueueMonitorAgent()
document_classifier = DocumentClassifierAgent()
entity_extractor = EntityExtractorAgent()
smart_chunker = SmartChunkerAgent()
embedding_generator = EmbeddingGeneratorAgent()
graph_builder = GraphBuilderAgent()
storage_coordinator = StorageCoordinatorAgent()

__all__ = [
    "queue_monitor",
    "document_classifier",
    "entity_extractor",
    "smart_chunker",
    "embedding_generator",
    "graph_builder",
    "storage_coordinator",
]
