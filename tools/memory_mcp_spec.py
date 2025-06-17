#!/usr/bin/env python3
"""
Script to create Memory & Learning MCP using mcp_factory programmatically.
This tests the boundaries of the MCP generator for complex MCPs.
"""

import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_memory_learning_mcp():
    """Create the Memory & Learning MCP specification"""
    
    # Since mcp_factory is interactive, we'll create the structure directly
    # to test if it can handle complex MCP requirements
    
    mcp_spec = {
        "name": "memory-learning",
        "display_name": "Memory & Learning System",
        "description": "Organizational memory and learning system with vector search and pattern recognition",
        "type": "internal",
        "language": "typescript",
        "version": "1.0.0",
        "tools": [
            {
                "name": "store_memory",
                "description": "Store experiences with embeddings in vector database",
                "parameters": {
                    "content": "string",
                    "type": "string",
                    "context": "object",
                    "team_id": "string",
                    "tags": "array"
                }
            },
            {
                "name": "retrieve_memories",
                "description": "Semantic search for relevant memories",
                "parameters": {
                    "query": "string",
                    "filters": "object",
                    "top_k": "number"
                }
            },
            {
                "name": "get_similar_experiences",
                "description": "Find related past situations",
                "parameters": {
                    "situation": "string",
                    "team_id": "string"
                }
            },
            {
                "name": "find_successful_patterns",
                "description": "Identify patterns that led to success",
                "parameters": {
                    "task_type": "string",
                    "min_confidence": "number"
                }
            },
            {
                "name": "analyze_outcome",
                "description": "Learn from action results",
                "parameters": {
                    "action": "string",
                    "result": "object",
                    "context": "object"
                }
            },
            {
                "name": "update_pattern_confidence",
                "description": "Adjust confidence based on new data",
                "parameters": {
                    "pattern_id": "string",
                    "success": "boolean"
                }
            },
            {
                "name": "get_team_insights",
                "description": "Analytics and insights per team",
                "parameters": {
                    "team_id": "string",
                    "timeframe": "string"
                }
            },
            {
                "name": "create_collection",
                "description": "Organize memory spaces",
                "parameters": {
                    "name": "string",
                    "description": "string",
                    "config": "object"
                }
            },
            {
                "name": "prune_old_memories",
                "description": "Manage memory retention",
                "parameters": {
                    "retention_policy": "object"
                }
            },
            {
                "name": "export_knowledge_base",
                "description": "Export knowledge for backup or sharing",
                "parameters": {
                    "format": "string",
                    "filters": "object"
                }
            }
        ],
        "resources": [
            {
                "name": "memory_stats",
                "description": "Current memory system statistics"
            },
            {
                "name": "learning_patterns",
                "description": "Discovered organizational patterns"
            },
            {
                "name": "team_knowledge_profiles",
                "description": "Knowledge expertise by team"
            }
        ],
        "environment": {
            "SUPABASE_URL": "${SUPABASE_URL}",
            "SUPABASE_KEY": "${SUPABASE_SERVICE_KEY}",
            "QDRANT_URL": "http://qdrant:6333",
            "QDRANT_API_KEY": "${QDRANT_API_KEY}",
            "EMBEDDING_MODEL": "text-embedding-ada-002",
            "OPENAI_API_KEY": "${OPENAI_API_KEY}"
        },
        "dependencies": {
            "qdrant": "For vector storage (using mock in dev)",
            "supabase": "For metadata storage",
            "openai": "For embeddings generation"
        }
    }
    
    print("Memory & Learning MCP Specification:")
    print("=" * 50)
    print(f"Name: {mcp_spec['name']}")
    print(f"Description: {mcp_spec['description']}")
    print(f"Tools: {len(mcp_spec['tools'])}")
    print(f"Resources: {len(mcp_spec['resources'])}")
    print("\nThis MCP will provide:")
    print("- Semantic memory storage and retrieval")
    print("- Pattern recognition and learning")
    print("- Cross-team knowledge sharing")
    print("- Continuous improvement tracking")
    print("\nNote: Will use MockQdrantClient until Qdrant is deployed")
    
    return mcp_spec

if __name__ == "__main__":
    spec = create_memory_learning_mcp()
    print("\nTo create this MCP manually:")
    print("1. Run: python tools/mcp_factory.py")
    print("2. Choose 'internal' MCP")
    print("3. Select 'custom' type")
    print("4. Use the specification above as reference")