#!/usr/bin/env python3
"""
Test the complete N8N integration end-to-end

This script tests:
1. Workflow registration
2. Workflow execution
3. Result retrieval
4. Error handling
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.n8n import N8NClient, WorkflowCategory
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

async def test_full_integration():
    """Test the complete N8N integration"""
    
    print("=" * 80)
    print("N8N INTEGRATION TEST")
    print("=" * 80)
    
    async with N8NClient() as client:
        # Step 1: Check if test workflow exists
        print("\n1. Checking test workflow registration...")
        workflow = await client.get_workflow_info("test-webhook-workflow")
        
        if not workflow:
            print("❌ Test workflow not found in registry")
            print("   Please run: python scripts/test_n8n_client.py --create-test-workflow")
            return
        
        print(f"✓ Found workflow: {workflow.name}")
        print(f"  - Owner: {workflow.owner_team}")
        print(f"  - Category: {workflow.category.value}")
        print(f"  - Active: {workflow.is_active}")
        print(f"  - Webhook URL: {workflow.webhook_url}")
        
        if not workflow.is_active:
            print("❌ Workflow is not active!")
            return
        
        # Step 2: Execute the workflow
        print("\n2. Executing test workflow...")
        test_data = {
            "message": "Hello from ELF Integration Test!",
            "timestamp": datetime.utcnow().isoformat(),
            "test_id": "integration-test-001"
        }
        
        print(f"   Sending data: {json.dumps(test_data, indent=2)}")
        
        try:
            execution = await client.execute_workflow(
                workflow_name="test-webhook-workflow",
                data=test_data,
                team_name="integration-test"
            )
            
            print(f"\n✓ Workflow executed successfully!")
            print(f"  - Execution ID: {execution.id}")
            print(f"  - Status: {execution.status.value}")
            print(f"  - Duration: {execution.duration:.2f}s" if execution.duration else "")
            
            if execution.output_data:
                print(f"\n   Output data:")
                print(json.dumps(execution.output_data, indent=2))
            
        except Exception as e:
            print(f"\n❌ Workflow execution failed: {e}")
            print("\nTroubleshooting:")
            print("1. Is the workflow active in n8n?")
            print("2. Is the webhook URL correct?")
            print("3. Can the client reach n8n service?")
            return
        
        # Step 3: Check execution history
        print("\n3. Checking execution history...")
        history = await client.get_execution_history(
            workflow_name="test-webhook-workflow",
            limit=5
        )
        
        print(f"   Found {len(history)} recent executions:")
        for exec in history:
            status_icon = "✓" if exec.status.value == "success" else "✗"
            print(f"   {status_icon} {exec.triggered_by} - {exec.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 4: Test error handling
        print("\n4. Testing error handling...")
        try:
            await client.execute_workflow(
                workflow_name="non-existent-workflow",
                data={},
                team_name="test"
            )
        except Exception as e:
            print(f"✓ Error handling works: {type(e).__name__}")
        
        # Step 5: Show workflow stats
        print("\n5. Workflow Statistics:")
        print("-" * 40)
        
        from supabase import create_client, Client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_SECRET_KEY')
        
        if supabase_url and supabase_key:
            supabase: Client = create_client(supabase_url, supabase_key)
            
            # Get stats from view
            stats = supabase.table('workflow_execution_stats').select('*').eq(
                'name', 'test-webhook-workflow'
            ).single().execute()
            
            if stats.data:
                stat = stats.data
                print(f"   Total executions: {stat['total_executions']}")
                print(f"   Successful: {stat['successful_executions']}")
                print(f"   Failed: {stat['failed_executions']}")
                
                if stat['total_executions'] > 0:
                    success_rate = (stat['successful_executions'] / stat['total_executions']) * 100
                    print(f"   Success rate: {success_rate:.1f}%")
                
                if stat['avg_duration_seconds']:
                    print(f"   Average duration: {stat['avg_duration_seconds']:.2f}s")
    
    print("\n" + "=" * 80)
    print("✅ N8N Integration Test Complete!")
    print("=" * 80)

async def quick_test():
    """Quick test to execute workflow"""
    async with N8NClient() as client:
        result = await client.execute_workflow(
            workflow_name="test-webhook-workflow",
            data={"message": "Quick test", "timestamp": datetime.utcnow().isoformat()},
            team_name="quick-test"
        )
        print(f"✓ Success! Output: {result.output_data}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test N8N Integration')
    parser.add_argument('--quick', action='store_true', help='Run quick test only')
    
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(quick_test())
    else:
        asyncio.run(test_full_integration())