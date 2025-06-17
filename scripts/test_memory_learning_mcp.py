#!/usr/bin/env python3
"""
Test script for the Memory & Learning MCP server.
Tests all 10 tools with mock data.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from elf_automations.shared.mcp.client import MCPClient


async def test_memory_learning_mcp():
    """Test the Memory & Learning MCP server"""
    print("🧠 Testing Memory & Learning MCP Server")
    print("=" * 50)
    
    # Initialize MCP client
    client = MCPClient(
        server_name="memory-learning",
        server_path=str(Path(__file__).parent.parent / "mcp-servers-ts" / "src" / "memory-learning" / "server.ts")
    )
    
    try:
        # Test 1: Store Memory
        print("\n1. Testing store_memory...")
        memory_result = await client.call_tool(
            "store_memory",
            {
                "content": "Successfully implemented blue-green deployment strategy reducing downtime to zero",
                "type": "learning",
                "context": {
                    "team": "devops",
                    "deployment_type": "blue-green",
                    "environment": "production",
                    "date": datetime.now().isoformat()
                },
                "team_id": "devops-team-123",
                "agent_name": "DevOps Manager",
                "tags": ["deployment", "zero-downtime", "blue-green"],
                "importance_score": 0.9
            }
        )
        print(f"✅ Memory stored: {json.dumps(memory_result, indent=2)}")
        
        # Test 2: Retrieve Memories
        print("\n2. Testing retrieve_memories...")
        retrieval_result = await client.call_tool(
            "retrieve_memories",
            {
                "query": "deployment strategies for zero downtime",
                "filters": {
                    "type": "learning",
                    "min_importance": 0.7
                },
                "top_k": 5
            }
        )
        print(f"✅ Memories retrieved: {retrieval_result.get('total_found', 0)} found")
        
        # Test 3: Get Similar Experiences
        print("\n3. Testing get_similar_experiences...")
        similar_result = await client.call_tool(
            "get_similar_experiences",
            {
                "situation": "Need to deploy critical security patch without service interruption",
                "min_similarity": 0.6
            }
        )
        print(f"✅ Similar experiences: {similar_result.get('message', 'No message')}")
        
        # Test 4: Find Successful Patterns
        print("\n4. Testing find_successful_patterns...")
        patterns_result = await client.call_tool(
            "find_successful_patterns",
            {
                "task_type": "deployment",
                "min_confidence": 0.7,
                "limit": 5
            }
        )
        print(f"✅ Patterns found: {patterns_result.get('total_found', 0)}")
        
        # Test 5: Analyze Outcome
        print("\n5. Testing analyze_outcome...")
        outcome_result = await client.call_tool(
            "analyze_outcome",
            {
                "action": "kubernetes rolling update",
                "result": {
                    "status": "completed",
                    "downtime": 0,
                    "rollback_required": False,
                    "deployment_time": 300
                },
                "context": {
                    "cluster": "production-east",
                    "replicas": 10,
                    "strategy": "rolling"
                },
                "success": True
            }
        )
        print(f"✅ Outcome analyzed: {outcome_result.get('analysis', {}).get('recommendation', 'No recommendation')}")
        
        # Test 6: Update Pattern Confidence
        if patterns_result.get('patterns') and len(patterns_result['patterns']) > 0:
            print("\n6. Testing update_pattern_confidence...")
            pattern_id = patterns_result['patterns'][0]['id']
            confidence_result = await client.call_tool(
                "update_pattern_confidence",
                {
                    "pattern_id": pattern_id,
                    "success": True
                }
            )
            print(f"✅ Pattern confidence updated: {confidence_result.get('new_confidence', 'Unknown')}")
        else:
            print("\n6. Skipping update_pattern_confidence (no patterns found)")
        
        # Test 7: Get Team Insights
        print("\n7. Testing get_team_insights...")
        insights_result = await client.call_tool(
            "get_team_insights",
            {
                "team_id": "devops-team-123",
                "timeframe": "month"
            }
        )
        print(f"✅ Team insights retrieved: {insights_result.get('insights', {}).get('statistics', {}).get('total_memories', 0)} memories")
        
        # Test 8: Create Collection
        print("\n8. Testing create_collection...")
        collection_result = await client.call_tool(
            "create_collection",
            {
                "name": "deployment-strategies",
                "description": "Collection of deployment strategies and best practices",
                "config": {
                    "retention_days": 365,
                    "auto_archive": True
                },
                "team_id": "devops-team-123"
            }
        )
        print(f"✅ Collection created: {collection_result.get('message', 'No message')}")
        
        # Test 9: Prune Old Memories (dry run)
        print("\n9. Testing prune_old_memories...")
        prune_result = await client.call_tool(
            "prune_old_memories",
            {
                "retention_policy": {
                    "days": 30,
                    "min_importance": 0.3
                },
                "dry_run": True
            }
        )
        print(f"✅ Prune test: Would delete {prune_result.get('would_delete', 0)} memories")
        
        # Test 10: Export Knowledge Base
        print("\n10. Testing export_knowledge_base...")
        export_result = await client.call_tool(
            "export_knowledge_base",
            {
                "format": "json",
                "filters": {
                    "team_id": "devops-team-123"
                }
            }
        )
        print(f"✅ Knowledge exported: {export_result.get('statistics', {}).get('memories_exported', 0)} memories")
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    # Note: This test assumes the MCP server is running
    print("\nNote: Make sure the Memory & Learning MCP server is running:")
    print("  cd mcp-servers-ts/src/memory-learning")
    print("  npm install")
    print("  npm run dev")
    print("\nOr this test will use the mock client.\n")
    
    asyncio.run(test_memory_learning_mcp())