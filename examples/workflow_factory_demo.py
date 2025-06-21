#!/usr/bin/env python3
"""
Workflow Factory Demo

Demonstrates the power of AI-powered workflow generation for business operations.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from tools.n8n_workflow_factory_v2 import EnhancedWorkflowFactory


async def demo_workflow_creation():
    """Demonstrate various workflow creation scenarios"""

    factory = EnhancedWorkflowFactory()

    # Example 1: Sales Report (should match report template)
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Sales Report Workflow")
    print("=" * 80)

    sales_workflow = await factory.create_workflow(
        description="Every Monday at 9am, fetch last week's sales data from our database, calculate top performers and revenue metrics, then send a report to the sales team Slack channel and email the executives",
        name="Weekly Sales Report",
        team="sales-team",
        category="automation",
    )

    print(f"\nTemplate Used: {sales_workflow['metadata']['template_used']}")
    print(f"Nodes: {len(sales_workflow['workflow']['nodes'])}")
    print(
        "Node Types:",
        [node["type"].split(".")[-1] for node in sales_workflow["workflow"]["nodes"]],
    )

    # Example 2: Customer Onboarding (custom workflow)
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Customer Onboarding Workflow")
    print("=" * 80)

    onboarding_workflow = await factory.create_workflow(
        description="When a new customer signs up via webhook, validate their data, create accounts in CRM and billing system, send welcome email, schedule follow-up call, and notify account manager on Slack",
        name="Customer Onboarding",
        team="customer-success",
        category="integration",
    )

    print(f"\nTemplate Used: {onboarding_workflow['metadata']['template_used']}")
    print(f"Nodes: {len(onboarding_workflow['workflow']['nodes'])}")
    print("Operations Detected:", onboarding_workflow["metadata"])

    # Example 3: Inventory Alert (should match ETL template)
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Inventory Alert Workflow")
    print("=" * 80)

    inventory_workflow = await factory.create_workflow(
        description="Every hour, check inventory levels in warehouse database, identify items below reorder threshold, generate purchase orders, and notify procurement team",
        name="Inventory Reorder Alert",
        team="operations-team",
        category="data-pipeline",
    )

    print(f"\nTemplate Used: {inventory_workflow['metadata']['template_used']}")
    print(f"Trigger Type: {inventory_workflow['metadata']['trigger_type']}")

    # Example 4: Expense Approval (should match approval template)
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Expense Approval Workflow")
    print("=" * 80)

    expense_workflow = await factory.create_workflow(
        description="Employee submits expense report, route to manager for amounts under $500, to director for $500-$5000, to CFO for over $5000, wait for approval, then process reimbursement",
        name="Expense Approval Process",
        team="finance-team",
        category="approval",
    )

    print(f"\nTemplate Used: {expense_workflow['metadata']['template_used']}")

    # Save examples
    examples_dir = Path(__file__).parent / "generated_workflows"
    examples_dir.mkdir(exist_ok=True)

    workflows = [
        ("sales_report", sales_workflow),
        ("customer_onboarding", onboarding_workflow),
        ("inventory_alert", inventory_workflow),
        ("expense_approval", expense_workflow),
    ]

    print("\n" + "=" * 80)
    print("SAVING WORKFLOWS")
    print("=" * 80)

    for filename, workflow_data in workflows:
        filepath = examples_dir / f"{filename}.json"
        with open(filepath, "w") as f:
            json.dump(workflow_data["workflow"], f, indent=2)
        print(f"✓ Saved: {filepath}")

    # Show batch processing capability
    print("\n" + "=" * 80)
    print("BATCH WORKFLOW GENERATION")
    print("=" * 80)

    batch_descriptions = [
        {
            "description": "Daily backup of production database to S3",
            "name": "Database Backup",
            "team": "devops-team",
        },
        {
            "description": "Monitor social media mentions and sentiment, alert on negative trends",
            "name": "Social Media Monitor",
            "team": "marketing-team",
        },
        {
            "description": "Sync employee data from HR system to Active Directory every 4 hours",
            "name": "HR AD Sync",
            "team": "it-team",
        },
    ]

    batch_results = await factory.generate_workflow_batch(batch_descriptions)

    print(f"\nGenerated {len(batch_results)} workflows in batch:")
    for result in batch_results:
        print(
            f"  - {result['workflow']['name']} ({result['metadata']['trigger_type']})"
        )


def show_statistics():
    """Show how this scales to hundreds of workflows"""

    print("\n" + "=" * 80)
    print("SCALING TO BUSINESS OPERATIONS")
    print("=" * 80)

    business_areas = {
        "Sales & Marketing": [
            "Lead scoring and routing",
            "Campaign performance reports",
            "Customer segmentation updates",
            "Competitor price monitoring",
            "Social media scheduling",
        ],
        "Finance & Accounting": [
            "Invoice processing",
            "Expense approvals",
            "Budget alerts",
            "Payment reconciliation",
            "Financial reporting",
        ],
        "Operations": [
            "Inventory management",
            "Supply chain alerts",
            "Quality control checks",
            "Maintenance scheduling",
            "Resource allocation",
        ],
        "HR & Admin": [
            "Onboarding workflows",
            "Leave approvals",
            "Performance reviews",
            "Training assignments",
            "Policy updates",
        ],
        "Customer Service": [
            "Ticket routing",
            "SLA monitoring",
            "Customer feedback analysis",
            "Knowledge base updates",
            "Escalation handling",
        ],
    }

    total_workflows = sum(len(workflows) for workflows in business_areas.values())

    print(f"\nPotential Workflows by Department:")
    for dept, workflows in business_areas.items():
        print(f"\n{dept}: {len(workflows)} workflows")
        for wf in workflows:
            print(f"  • {wf}")

    print(f"\n📊 Total Potential Workflows: {total_workflows}")
    print(f"🚀 At 70% automation rate: {int(total_workflows * 0.7)} active workflows")
    print(
        f"⏱️  If each saves 2 hours/week: {int(total_workflows * 0.7 * 2)} hours saved weekly"
    )
    print(f"💰 At $50/hour: ${int(total_workflows * 0.7 * 2 * 50):,} saved per week")


if __name__ == "__main__":
    print("🤖 N8N Workflow Factory Demo")
    print("Showing how AI can generate workflows for business operations")

    # Run the demo
    asyncio.run(demo_workflow_creation())

    # Show scaling potential
    show_statistics()

    print("\n✅ Demo Complete!")
    print("\nNext Steps:")
    print("1. Import generated workflows into n8n")
    print("2. Customize with actual API endpoints and credentials")
    print("3. Test and activate")
    print("4. Monitor execution and optimize")
