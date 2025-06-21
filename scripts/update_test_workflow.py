#!/usr/bin/env python3
"""
Update test workflow with actual n8n workflow ID
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def update_workflow(n8n_workflow_id: str):
    """Update the test workflow with actual n8n ID"""

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

    # Update the workflow
    result = (
        supabase.table("n8n_workflows")
        .update(
            {
                "n8n_workflow_id": n8n_workflow_id,
                "webhook_url": f"http://n8n.n8n.svc.cluster.local:5678/webhook/{n8n_workflow_id}",
            }
        )
        .eq("name", "test-webhook-workflow")
        .execute()
    )

    if result.data:
        print(f"✓ Updated test workflow with n8n ID: {n8n_workflow_id}")
        print(
            f"  Webhook URL: http://n8n.n8n.svc.cluster.local:5678/webhook/{n8n_workflow_id}"
        )
    else:
        print("✗ Failed to update workflow")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_test_workflow.py <n8n-workflow-id>")
        print("Example: python update_test_workflow.py abc123def456")
        sys.exit(1)

    update_workflow(sys.argv[1])
