#!/usr/bin/env python3
"""
Demo Script: N8N Workflow Import/Export

Demonstrates the new workflow import/export capabilities including:
- Importing workflows from JSON, files, and URLs
- Validating and processing workflows
- Exporting workflows in various formats
- Batch operations
"""

import asyncio
import json
import os
from pathlib import Path

from elf_automations.shared.n8n import N8NClient
from elf_automations.shared.utils.database import get_supabase_client


async def main():
    """Run workflow import/export demos"""

    # Initialize client
    client = N8NClient()

    print("🚀 N8N Workflow Import/Export Demo")
    print("=" * 50)

    # 1. Import from JSON
    print("\n📥 Demo 1: Import from JSON")
    print("-" * 30)

    sample_workflow = {
        "name": "Demo Webhook to Slack",
        "nodes": [
            {
                "parameters": {
                    "path": "/demo-webhook",
                    "responseMode": "onReceived",
                    "responseData": "allEntries",
                    "responsePropertyName": "data",
                    "options": {},
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "id": "webhook_1",
            },
            {
                "parameters": {
                    "channel": "general",
                    "text": "New webhook received: {{$json.message}}",
                    "authentication": "credential",
                    "credential": {"name": "slack_api"},
                },
                "name": "Send to Slack",
                "type": "n8n-nodes-base.slack",
                "typeVersion": 1,
                "position": [450, 300],
                "id": "slack_1",
            },
        ],
        "connections": {
            "Webhook": {
                "main": [[{"node": "Send to Slack", "type": "main", "index": 0}]]
            }
        },
        "settings": {"executionOrder": "v1"},
    }

    result = await client.import_workflow(
        source=json.dumps(sample_workflow),
        source_type="json",
        owner_team="demo-team",
        category="webhooks",
        validate=True,
        process=True,
        auto_fix=True,
    )

    if result["success"]:
        print(f"✅ Workflow imported successfully!")
        print(f"   ID: {result['workflow_id']}")
        if result["validation_report"]:
            report = result["validation_report"]
            print(f"   Validation: {report['status']}")
            if report.get("warnings"):
                print("   ⚠️  Warnings:")
                for warning in report["warnings"]:
                    print(f"      - {warning['message']}")
    else:
        print(f"❌ Import failed: {result.get('error', 'Unknown error')}")

    # 2. Import from URL
    print("\n📥 Demo 2: Import from URL")
    print("-" * 30)

    # This would be a real URL in production
    demo_url = "https://example.com/workflows/sample-etl.json"
    print(f"Importing from: {demo_url}")
    print("(Simulated - would fetch from actual URL)")

    # 3. Export workflow
    if result["success"]:
        workflow_id = result["workflow_id"]

        print(f"\n📤 Demo 3: Export Workflow")
        print("-" * 30)

        # Export as JSON
        export_data = client.export_workflow(
            workflow_id=workflow_id, include_metadata=True
        )

        print("Exported workflow:")
        print(f"  Name: {export_data['metadata']['name']}")
        print(f"  Category: {export_data['metadata']['category']}")
        print(f"  Nodes: {len(export_data['workflow']['nodes'])}")

        # Export to file
        output_path = client.export_to_file(
            workflow_id=workflow_id, output_path="exports/demo_workflow.json"
        )
        print(f"\n💾 Saved to: {output_path}")

    # 4. Batch export
    print(f"\n📤 Demo 4: Batch Export")
    print("-" * 30)

    exported = client.exporter.export_batch(category="webhooks", include_metadata=True)

    print(f"Exported {len(exported)} workflows from 'webhooks' category")

    # 5. Validation demo
    print(f"\n✅ Demo 5: Workflow Validation")
    print("-" * 30)

    # Invalid workflow with issues
    invalid_workflow = {
        "name": "Problematic Workflow",
        "nodes": [
            {
                "type": "n8n-nodes-base.httpRequest",
                "parameters": {
                    "url": "http://insecure-api.com/data",  # HTTP instead of HTTPS
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "httpHeaderAuth": {
                        "name": "API-Key",
                        "value": "sk-1234567890abcdef",  # Hardcoded credential
                    },
                },
            }
        ],
    }

    validation_result = client.validate_workflow(
        workflow_json=invalid_workflow, owner_team="demo-team"
    )

    print("Validation Results:")
    print(f"  Status: {validation_result['status']}")
    if validation_result.get("security_issues"):
        print("  🔒 Security Issues:")
        for issue in validation_result["security_issues"]:
            print(f"     - {issue['type']}: {issue['severity']}")
    if validation_result.get("suggestions"):
        print("  💡 Suggestions:")
        for suggestion in validation_result["suggestions"]:
            print(f"     - {suggestion}")

    # 6. Export formats
    print(f"\n📄 Demo 6: Export Formats")
    print("-" * 30)

    if result["success"]:
        # Export as different formats
        formats = ["json", "yaml", "markdown", "archive"]

        for format in formats:
            try:
                content, filename = await client.exporter.export_workflow(
                    workflow_id, format=format
                )
                if content:
                    print(f"✅ Exported as {format}: {filename}")
            except Exception as e:
                print(f"❌ Failed to export as {format}: {e}")

    print("\n✨ Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
