#!/usr/bin/env python3
"""
Test script to demonstrate resource state transitions
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import Client, create_client

from elf_automations.shared.state_manager import (
    MCPStateManager,
    StateTracker,
    TeamStateManager,
    WorkflowStateManager,
)

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Create Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SECRET_KEY")

    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")

    return create_client(url, key)


def demo_workflow_lifecycle():
    """Demonstrate workflow state transitions"""
    print("\n🔄 Workflow Lifecycle Demo")
    print("=" * 50)

    supabase = get_supabase_client()
    workflow_mgr = WorkflowStateManager(supabase)
    tracker = StateTracker(supabase)

    # Create a test workflow
    workflow_id = str(uuid.uuid4())
    workflow_name = f"Test Workflow {datetime.now().strftime('%H:%M:%S')}"

    print(f"\n1. Creating workflow: {workflow_name}")

    # Register workflow
    success, error = workflow_mgr.register_workflow(
        workflow_id, workflow_name, "test-team", "demo-script"
    )
    print(f"   ✅ Registered: {success}" if success else f"   ❌ Failed: {error}")

    # Start validation
    if success:
        print("\n2. Starting validation...")
        success, error = workflow_mgr.start_validation(
            workflow_id, workflow_name, "validation-service"
        )
        print(f"   ✅ Validation started" if success else f"   ❌ Failed: {error}")

    # Complete validation
    if success:
        print("\n3. Completing validation...")
        validation_report = {
            "errors": [],
            "warnings": ["Consider adding error handling"],
            "checks_passed": 10,
            "checks_total": 10,
        }
        success, error = workflow_mgr.complete_validation(
            workflow_id, workflow_name, True, validation_report, "validation-service"
        )
        print(f"   ✅ Validation passed" if success else f"   ❌ Failed: {error}")

    # Deploy workflow
    if success:
        print("\n4. Deploying to N8N...")
        n8n_id = f"n8n-{uuid.uuid4().hex[:8]}"
        success, error = workflow_mgr.deploy_workflow(
            workflow_id, workflow_name, n8n_id, "deployment-service"
        )
        print(
            f"   ✅ Deployed with N8N ID: {n8n_id}"
            if success
            else f"   ❌ Failed: {error}"
        )

    # Activate workflow
    if success:
        print("\n5. Activating workflow...")
        success, error = workflow_mgr.activate_workflow(
            workflow_id, workflow_name, "admin@example.com"
        )
        print(f"   ✅ Workflow active!" if success else f"   ❌ Failed: {error}")

    # Show current state
    print("\n6. Current state:")
    details = tracker.get_resource_details("workflow", workflow_id)
    if details["current_state"]:
        print(f"   State: {details['current_state']['current_state']}")
        print(f"   Reason: {details['current_state']['state_reason']}")
        print(f"   Last transition: {details['current_state']['transitioned_at']}")

    # Show history
    print("\n7. State history:")
    for transition in details["history"][:5]:
        print(
            f"   {transition['from_state']} → {transition['to_state']} "
            + f"({transition['transitioned_by']}) - {transition['transition_reason']}"
        )

    return workflow_id


def demo_mcp_lifecycle():
    """Demonstrate MCP state transitions"""
    print("\n🔌 MCP Server Lifecycle Demo")
    print("=" * 50)

    supabase = get_supabase_client()
    mcp_mgr = MCPStateManager(supabase)

    # Create a test MCP
    mcp_id = str(uuid.uuid4())
    mcp_name = f"test-mcp-{datetime.now().strftime('%H%M%S')}"

    print(f"\n1. Creating MCP: {mcp_name}")

    # Register MCP
    success, error = mcp_mgr.register_mcp(
        mcp_id, mcp_name, "server", "test-category", "demo-script"
    )
    print(f"   ✅ Registered" if success else f"   ❌ Failed: {error}")

    # Build image
    if success:
        print("\n2. Building Docker image...")
        success, error = mcp_mgr.build_image(mcp_id, mcp_name, "build-system")
        print(f"   ✅ Build started" if success else f"   ❌ Failed: {error}")

    # Complete build
    if success:
        print("\n3. Build completed...")
        success, error = mcp_mgr.complete_build(
            mcp_id, mcp_name, True, f"{mcp_name}:v1.0", "build-system"
        )
        print(f"   ✅ Image ready" if success else f"   ❌ Failed: {error}")

    return mcp_id


def show_resource_overview():
    """Show current resource overview"""
    print("\n📊 Resource Overview")
    print("=" * 50)

    supabase = get_supabase_client()
    tracker = StateTracker(supabase)

    # Get overview
    overview = tracker.get_resource_overview()

    for resource_type, states in overview.items():
        print(f"\n{resource_type.upper()}:")
        total = sum(state_info["count"] for state_info in states.values())
        print(f"  Total: {total}")
        for state, info in states.items():
            print(f"  - {state}: {info['count']}")

    # Get resources awaiting action
    awaiting = tracker.get_resources_awaiting_action()
    if awaiting:
        print(f"\n⚠️  Resources Awaiting Action: {len(awaiting)}")
        for resource in awaiting[:5]:
            print(
                f"  - {resource['resource_name']} ({resource['resource_type']}) - {resource['current_state']}"
            )

    # Get deployment readiness
    readiness = tracker.get_deployment_readiness()
    print("\n🚀 Deployment Readiness:")
    for resource_type, info in readiness.items():
        if info["ready"] > 0 or info["blocked"] > 0:
            print(
                f"  {resource_type}: {info['ready']} ready, {info['blocked']} blocked"
            )


def main():
    """Run demonstration"""
    print("Resource State Management Demo")
    print("=" * 50)

    try:
        # Show current state
        show_resource_overview()

        # Demo workflow lifecycle
        workflow_id = demo_workflow_lifecycle()

        # Demo MCP lifecycle
        mcp_id = demo_mcp_lifecycle()

        # Show updated overview
        print("\n" + "=" * 50)
        show_resource_overview()

        print("\n✅ Demo completed successfully!")
        print(f"\nCreated resources:")
        print(f"  - Workflow ID: {workflow_id}")
        print(f"  - MCP ID: {mcp_id}")
        print("\nCheck the Control Center Resources page to see these in the UI!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
