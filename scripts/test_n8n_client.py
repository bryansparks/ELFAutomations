#!/usr/bin/env python3
"""
Test N8N Client SDK

This script tests the basic functionality of the N8N client.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from elf_automations.shared.n8n import N8NClient, WorkflowCategory

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


async def test_client():
    """Test N8N client functionality"""

    print("Testing N8N Client SDK...")
    print("-" * 50)

    # Create client
    async with N8NClient() as client:
        # Test 1: List workflows
        print("\n1. Listing workflows...")
        try:
            workflows = await client.list_workflows()
            print(f"   Found {len(workflows)} workflows")
            for wf in workflows:
                print(f"   - {wf.name} ({wf.category.value}) by {wf.owner_team}")
        except Exception as e:
            print(f"   Error: {e}")

        # Test 2: Get specific workflow
        print("\n2. Getting workflow info...")
        try:
            workflow_name = "test-webhook-workflow"
            info = await client.get_workflow_info(workflow_name)
            if info:
                print(f"   Found workflow: {info.name}")
                print(f"   - Description: {info.description}")
                print(f"   - Trigger: {info.trigger_type.value}")
                print(f"   - Active: {info.is_active}")
            else:
                print(f"   Workflow '{workflow_name}' not found")
        except Exception as e:
            print(f"   Error: {e}")

        # Test 3: Get execution history
        print("\n3. Getting execution history...")
        try:
            executions = await client.get_execution_history(limit=5)
            print(f"   Found {len(executions)} recent executions")
            for exec in executions:
                print(
                    f"   - {exec.workflow_name} by {exec.triggered_by} - {exec.status.value}"
                )
        except Exception as e:
            print(f"   Error: {e}")

        # Test 4: Execute workflow (only if test workflow exists)
        print("\n4. Testing workflow execution...")
        try:
            # Check if test workflow exists
            test_workflow = await client.get_workflow_info("test-webhook-workflow")
            if test_workflow and test_workflow.is_active:
                print("   Executing test workflow...")
                result = await client.execute_workflow(
                    workflow_name="test-webhook-workflow",
                    data={
                        "message": "Hello from ELF test!",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    team_name="test-script",
                )
                print(f"   ✓ Execution completed: {result.status.value}")
                if result.output_data:
                    print(f"   Output: {result.output_data}")
            else:
                print("   ! Test workflow not found or inactive")
                print("   Create a test workflow in n8n first:")
                print("   - Name: test-webhook-workflow")
                print("   - Trigger: Webhook")
                print("   - Add to registry using:")
                print("     INSERT INTO n8n_workflows (...) VALUES (...)")
        except Exception as e:
            print(f"   Error: {e}")

    print("\n" + "-" * 50)
    print("Testing complete!")


async def create_test_workflow():
    """Helper to create a test workflow entry in the registry"""

    from supabase import Client, create_client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_SECRET_KEY")
    )

    if not supabase_url or not supabase_key:
        print("Error: Supabase credentials not set")
        return

    supabase: Client = create_client(supabase_url, supabase_key)

    # Sample test workflow
    test_workflow = {
        "name": "test-webhook-workflow",
        "description": "Test webhook workflow for SDK testing",
        "category": "automation",
        "owner_team": "test-team",
        "n8n_workflow_id": "test-123",
        "trigger_type": "webhook",
        "webhook_url": "http://n8n.n8n.svc.cluster.local:5678/webhook/test",
        "input_schema": {"message": "string", "timestamp": "string"},
        "output_schema": {"result": "string", "processed_at": "string"},
    }

    try:
        result = supabase.table("n8n_workflows").insert(test_workflow).execute()
        print("✓ Test workflow created successfully")
        print(f"  ID: {result.data[0]['id']}")
    except Exception as e:
        print(f"Error creating test workflow: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test N8N Client SDK")
    parser.add_argument(
        "--create-test-workflow",
        action="store_true",
        help="Create a test workflow in the registry",
    )

    args = parser.parse_args()

    if args.create_test_workflow:
        asyncio.run(create_test_workflow())
    else:
        asyncio.run(test_client())
