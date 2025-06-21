#!/usr/bin/env python3
"""
Pattern-Based Workflow Generation Demo

Demonstrates the new pattern detection and smart service selection.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.n8n.config import (
    WorkflowConfig,
    create_engineering_team_config,
    create_marketing_team_config,
)
from elf_automations.shared.n8n.patterns import WorkflowPatterns, detect_pattern
from tools.n8n_workflow_factory_v2 import EnhancedWorkflowFactory


async def demo_pattern_workflows():
    """Generate workflows using pattern detection"""

    # Set up team configurations
    config = WorkflowConfig()
    config.set_team_config(create_marketing_team_config())
    config.set_team_config(create_engineering_team_config())

    # Example workflows to generate
    workflows = [
        {
            "description": "Monitor Gmail inbox for customer inquiries, categorize them using AI, store in Supabase, and send Slack notifications for urgent items",
            "name": "Customer Email Triage",
            "team": "marketing",
            "category": "email_management",
        },
        {
            "description": "Receive SMS messages via Twilio, analyze sentiment, route to appropriate team member, and auto-respond with acknowledgment",
            "name": "SMS Support Hub",
            "team": "support",
            "category": "communication",
        },
        {
            "description": "Every Monday at 9am, pull sales data from Supabase, generate report in Google Sheets, create summary in Google Docs, and email to executives",
            "name": "Weekly Sales Report",
            "team": "sales",
            "category": "reporting",
        },
        {
            "description": "Multi-channel support system that monitors email, SMS, and Slack for customer messages, uses AI to categorize and prioritize, then routes to agents",
            "name": "Unified Support Portal",
            "team": "support",
            "category": "customer_service",
        },
        {
            "description": "Collect form submissions from website, validate data, store in both Supabase and Google Sheets, send confirmation email via Gmail",
            "name": "Lead Collection Pipeline",
            "team": "marketing",
            "category": "data_collection",
        },
    ]

    print("🚀 Pattern-Based Workflow Generation Demo")
    print("=" * 60)

    for workflow_spec in workflows:
        print(f"\n📝 Generating: {workflow_spec['name']}")
        print(f"   Team: {workflow_spec['team']}")
        print(f"   Pattern Detection...")

        # Create factory for the team
        factory = EnhancedWorkflowFactory(team_name=workflow_spec["team"])

        try:
            # Generate workflow using pattern detection
            result = await factory.create_pattern_workflow(
                description=workflow_spec["description"],
                name=workflow_spec["name"],
                team=workflow_spec["team"],
                category=workflow_spec["category"],
            )

            print(f"   ✅ Success! Pattern: {result['metadata']['pattern']}")
            print(
                f"   📂 Saved to: generated_workflows/{workflow_spec['category']}/{workflow_spec['name'].lower().replace(' ', '_')}.json"
            )

            # Show services used
            services = result["metadata"].get("services", {})
            if services:
                print("   🔧 Services configured:")
                for service_type, service_name in services.items():
                    if service_name:
                        print(f"      - {service_type}: {service_name}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

    print("\n" + "=" * 60)
    print("✨ Demo complete! Check generated_workflows/ for results")


def show_available_patterns():
    """Display all available workflow patterns"""

    print("\n📚 Available Workflow Patterns:")
    print("=" * 60)

    patterns = [
        WorkflowPatterns.input_process_output(),
        WorkflowPatterns.email_management(),
        WorkflowPatterns.sms_communication(),
        WorkflowPatterns.approval_workflow(),
        WorkflowPatterns.data_pipeline(),
        WorkflowPatterns.report_generation(),
        WorkflowPatterns.customer_support(),
        WorkflowPatterns.data_collection(),
    ]

    for pattern in patterns:
        print(f"\n🎯 {pattern.name}")
        print(f"   {pattern.description}")
        print(f"   Inputs: {', '.join([inp.value for inp in pattern.inputs])}")
        print(f"   Storage: {', '.join([stor.value for stor in pattern.storage])}")
        print(f"   Outputs: {', '.join([out.value for out in pattern.outputs])}")
        if pattern.requires_ai:
            print("   🤖 Requires AI processing")
        if pattern.requires_approval:
            print("   ✅ Includes approval flow")


def test_pattern_detection():
    """Test pattern detection on various descriptions"""

    print("\n🔍 Testing Pattern Detection:")
    print("=" * 60)

    test_cases = [
        "Monitor emails and categorize them",
        "Send SMS notifications when orders are placed",
        "Approve expense reports over $1000",
        "Extract data from API and load into database",
        "Generate weekly performance reports",
        "Handle customer support tickets from multiple channels",
        "Collect survey responses and analyze them",
    ]

    for description in test_cases:
        pattern = detect_pattern(description)
        print(f"\n📝 '{description}'")
        print(f"   → Pattern: {pattern.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pattern Workflow Demo")
    parser.add_argument(
        "--show-patterns", action="store_true", help="Show available patterns"
    )
    parser.add_argument(
        "--test-detection", action="store_true", help="Test pattern detection"
    )
    parser.add_argument(
        "--generate", action="store_true", help="Generate example workflows"
    )

    args = parser.parse_args()

    if args.show_patterns:
        show_available_patterns()
    elif args.test_detection:
        test_pattern_detection()
    elif args.generate:
        asyncio.run(demo_pattern_workflows())
    else:
        # Run all demos
        show_available_patterns()
        test_pattern_detection()
        print("\n" + "=" * 80)
        input("\nPress Enter to generate example workflows...")
        asyncio.run(demo_pattern_workflows())
