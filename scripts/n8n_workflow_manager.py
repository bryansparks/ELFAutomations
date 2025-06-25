#!/usr/bin/env python3
"""
N8N Workflow Manager

Command-line tool for managing n8n workflows in the ELF system.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import Client, create_client

from elf_automations.shared.n8n import N8NClient, WorkflowCategory, WorkflowTriggerType

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class WorkflowManager:
    """Manage n8n workflows in the registry"""

    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = (
            os.getenv("SUPABASE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_SECRET_KEY")
        )

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Supabase credentials not set. Set SUPABASE_URL and SUPABASE_KEY (or SUPABASE_ANON_KEY) in .env"
            )

        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.client = N8NClient()

    def register_workflow(
        self,
        name: str,
        description: str,
        category: str,
        owner_team: str,
        n8n_workflow_id: str,
        trigger_type: str,
        webhook_url: Optional[str] = None,
        input_schema: Optional[dict] = None,
        output_schema: Optional[dict] = None,
    ):
        """Register a new workflow in the system"""

        workflow_data = {
            "name": name,
            "description": description,
            "category": category,
            "owner_team": owner_team,
            "n8n_workflow_id": n8n_workflow_id,
            "trigger_type": trigger_type,
            "webhook_url": webhook_url,
            "input_schema": input_schema or {},
            "output_schema": output_schema or {},
            "is_active": True,
        }

        try:
            result = (
                self.supabase.table("n8n_workflows").insert(workflow_data).execute()
            )
            print(f"✓ Workflow '{name}' registered successfully")
            print(f"  ID: {result.data[0]['id']}")
            return result.data[0]
        except Exception as e:
            print(f"✗ Error registering workflow: {e}")
            return None

    def update_workflow(self, name: str, **kwargs):
        """Update workflow properties"""

        try:
            # Get current workflow
            current = (
                self.supabase.table("n8n_workflows")
                .select("*")
                .eq("name", name)
                .single()
                .execute()
            )

            if not current.data:
                print(f"✗ Workflow '{name}' not found")
                return None

            # Update fields
            update_data = {k: v for k, v in kwargs.items() if v is not None}

            result = (
                self.supabase.table("n8n_workflows")
                .update(update_data)
                .eq("name", name)
                .execute()
            )
            print(f"✓ Workflow '{name}' updated successfully")
            return result.data[0]
        except Exception as e:
            print(f"✗ Error updating workflow: {e}")
            return None

    def activate_workflow(self, name: str):
        """Activate a workflow"""
        return self.update_workflow(name, is_active=True)

    def deactivate_workflow(self, name: str):
        """Deactivate a workflow"""
        return self.update_workflow(name, is_active=False)

    async def list_workflows(
        self, team: Optional[str] = None, category: Optional[str] = None
    ):
        """List workflows with optional filters"""

        async with self.client as client:
            workflows = await client.list_workflows(
                owner_team=team,
                category=WorkflowCategory(category) if category else None,
            )

            print(f"\nFound {len(workflows)} workflows")
            print("-" * 80)

            for wf in workflows:
                status = "✓" if wf.is_active else "✗"
                print(f"{status} {wf.name}")
                print(f"  Owner: {wf.owner_team}")
                print(f"  Category: {wf.category.value}")
                print(f"  Trigger: {wf.trigger_type.value}")
                print(f"  Description: {wf.description}")
                print()

    async def show_stats(self):
        """Show workflow statistics"""

        # Get stats from view
        result = self.supabase.table("workflow_execution_stats").select("*").execute()

        print("\nWorkflow Statistics")
        print("-" * 80)

        total_executions = 0
        total_success = 0
        total_failed = 0

        for stat in result.data:
            print(f"\n{stat['name']} ({stat['owner_team']})")
            print(f"  Total executions: {stat['total_executions']}")
            print(f"  Success: {stat['successful_executions']}")
            print(f"  Failed: {stat['failed_executions']}")
            print(f"  Running: {stat['running_executions']}")

            if stat["avg_duration_seconds"]:
                print(f"  Avg duration: {stat['avg_duration_seconds']:.2f}s")

            if stat["total_executions"] > 0:
                success_rate = (
                    stat["successful_executions"] / stat["total_executions"]
                ) * 100
                print(f"  Success rate: {success_rate:.1f}%")

            total_executions += stat["total_executions"] or 0
            total_success += stat["successful_executions"] or 0
            total_failed += stat["failed_executions"] or 0

        print("\n" + "-" * 80)
        print(f"Total executions: {total_executions}")
        print(f"Total success: {total_success}")
        print(f"Total failed: {total_failed}")

        if total_executions > 0:
            overall_success_rate = (total_success / total_executions) * 100
            print(f"Overall success rate: {overall_success_rate:.1f}%")


async def main():
    """Main CLI interface"""

    import argparse

    parser = argparse.ArgumentParser(description="N8N Workflow Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Register command
    register_parser = subparsers.add_parser("register", help="Register a new workflow")
    register_parser.add_argument("name", help="Workflow name")
    register_parser.add_argument(
        "--description", required=True, help="Workflow description"
    )
    register_parser.add_argument(
        "--category",
        required=True,
        choices=[
            "data-pipeline",
            "integration",
            "automation",
            "notification",
            "approval",
        ],
    )
    register_parser.add_argument("--team", required=True, help="Owner team")
    register_parser.add_argument("--workflow-id", required=True, help="N8N workflow ID")
    register_parser.add_argument(
        "--trigger", required=True, choices=["webhook", "schedule", "manual", "event"]
    )
    register_parser.add_argument("--webhook-url", help="Webhook URL for trigger")
    register_parser.add_argument("--input-schema", help="JSON input schema")
    register_parser.add_argument("--output-schema", help="JSON output schema")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update workflow")
    update_parser.add_argument("name", help="Workflow name")
    update_parser.add_argument("--description", help="New description")
    update_parser.add_argument("--webhook-url", help="New webhook URL")
    update_parser.add_argument("--input-schema", help="New input schema (JSON)")
    update_parser.add_argument("--output-schema", help="New output schema (JSON)")

    # Activate/Deactivate commands
    activate_parser = subparsers.add_parser("activate", help="Activate workflow")
    activate_parser.add_argument("name", help="Workflow name")

    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate workflow")
    deactivate_parser.add_argument("name", help="Workflow name")

    # List command
    list_parser = subparsers.add_parser("list", help="List workflows")
    list_parser.add_argument("--team", help="Filter by team")
    list_parser.add_argument("--category", help="Filter by category")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show workflow statistics")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import workflow from file")
    import_parser.add_argument("file", help="Path to workflow JSON file")
    import_parser.add_argument("--name", help="Override workflow name")
    import_parser.add_argument(
        "--category",
        required=True,
        choices=[
            "customer-onboarding",
            "order-processing",
            "data-pipeline",
            "data-sync",
            "reporting",
            "marketing-automation",
            "team-coordination",
            "maintenance",
            "integration",
            "notification",
            "approval",
            "automation",
            "other",
        ],
    )
    import_parser.add_argument("--team", required=True, help="Owner team")
    import_parser.add_argument("--description", help="Workflow description")
    import_parser.add_argument("--tags", nargs="+", help="Tags for the workflow")
    import_parser.add_argument(
        "--validate", action="store_true", help="Validate after import"
    )

    # Export command
    export_parser = subparsers.add_parser("export", help="Export workflow to file")
    export_parser.add_argument("workflow", help="Workflow name or ID")
    export_parser.add_argument("--output", help="Output file path")
    export_parser.add_argument("--version", type=int, help="Export specific version")
    export_parser.add_argument(
        "--no-metadata", action="store_true", help="Export without metadata"
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate workflow")
    validate_parser.add_argument("workflow", help="Workflow name, ID, or JSON file")
    validate_parser.add_argument(
        "--deep", action="store_true", help="Perform deep validation"
    )
    validate_parser.add_argument("--team", help="Team for permission checks")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync workflows with N8N")
    sync_parser.add_argument("--all", action="store_true", help="Sync all workflows")
    sync_parser.add_argument(
        "--workflows", nargs="+", help="Specific workflow IDs to sync"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = WorkflowManager()

    if args.command == "register":
        input_schema = json.loads(args.input_schema) if args.input_schema else None
        output_schema = json.loads(args.output_schema) if args.output_schema else None

        manager.register_workflow(
            name=args.name,
            description=args.description,
            category=args.category,
            owner_team=args.team,
            n8n_workflow_id=args.workflow_id,
            trigger_type=args.trigger,
            webhook_url=args.webhook_url,
            input_schema=input_schema,
            output_schema=output_schema,
        )

    elif args.command == "update":
        kwargs = {}
        if args.description:
            kwargs["description"] = args.description
        if args.webhook_url:
            kwargs["webhook_url"] = args.webhook_url
        if args.input_schema:
            kwargs["input_schema"] = json.loads(args.input_schema)
        if args.output_schema:
            kwargs["output_schema"] = json.loads(args.output_schema)

        manager.update_workflow(args.name, **kwargs)

    elif args.command == "activate":
        manager.activate_workflow(args.name)

    elif args.command == "deactivate":
        manager.deactivate_workflow(args.name)

    elif args.command == "list":
        await manager.list_workflows(args.team, args.category)

    elif args.command == "stats":
        await manager.show_stats()

    elif args.command == "import":
        # Import workflow from file
        async with manager.client as client:
            try:
                # Normalize category
                category = args.category.replace("-", "_")

                result = client.import_from_file(
                    file_path=args.file,
                    name=args.name,
                    category=category,
                    owner_team=args.team,
                    imported_by="cli",
                    description=args.description,
                    tags=args.tags,
                )

                print(f"✓ Workflow imported successfully")
                print(f"  ID: {result['id']}")
                print(f"  Slug: {result['slug']}")
                print(f"  Status: {result['status']}")

                # Validate if requested
                if args.validate:
                    print("\nValidating workflow...")
                    validation = client.validate_workflow(
                        workflow_json=result["n8n_workflow_json"],
                        owner_team=args.team,
                        deep_validation=True,
                    )

                    print(f"\nValidation Status: {validation['status']}")
                    if validation["summary"]["error_count"] > 0:
                        print(f"  Errors: {validation['summary']['error_count']}")
                        for error in validation["errors"]:
                            print(f"    - {error['message']}")
                    if validation["summary"]["warning_count"] > 0:
                        print(f"  Warnings: {validation['summary']['warning_count']}")
                        for warning in validation["warnings"][:5]:  # Show first 5
                            print(f"    - {warning['message']}")

            except Exception as e:
                print(f"✗ Import failed: {e}")

    elif args.command == "export":
        # Export workflow to file
        async with manager.client as client:
            try:
                # Determine if input is ID (UUID) or name
                import uuid

                workflow_id = None
                workflow_slug = None

                try:
                    uuid.UUID(args.workflow)
                    workflow_id = args.workflow
                except ValueError:
                    workflow_slug = args.workflow

                output_path = client.export_to_file(
                    workflow_id=workflow_id,
                    workflow_slug=workflow_slug,
                    output_path=args.output,
                    version=args.version,
                    include_metadata=not args.no_metadata,
                )

                print(f"✓ Workflow exported to: {output_path}")

            except Exception as e:
                print(f"✗ Export failed: {e}")

    elif args.command == "validate":
        # Validate workflow
        async with manager.client as client:
            try:
                # Check if input is a file
                if args.workflow.endswith(".json"):
                    with open(args.workflow, "r") as f:
                        workflow_json = json.load(f)
                else:
                    # Get workflow from database
                    import uuid

                    try:
                        uuid.UUID(args.workflow)
                        workflow = client.export_workflow(
                            workflow_id=args.workflow, include_metadata=False
                        )
                    except ValueError:
                        workflow = client.export_workflow(
                            workflow_slug=args.workflow, include_metadata=False
                        )

                    workflow_json = workflow

                # Validate
                validation = client.validate_workflow(
                    workflow_json=workflow_json,
                    owner_team=args.team,
                    deep_validation=args.deep,
                )

                print(f"Validation Status: {validation['status']}")
                print(f"\nSummary:")
                print(f"  Errors: {validation['summary']['error_count']}")
                print(f"  Warnings: {validation['summary']['warning_count']}")
                print(f"  Suggestions: {validation['summary']['suggestion_count']}")
                print(
                    f"  Security Issues: {validation['summary']['security_issue_count']}"
                )

                if validation["errors"]:
                    print("\nErrors:")
                    for error in validation["errors"]:
                        print(f"  - [{error['code']}] {error['message']}")

                if validation["security_issues"]:
                    print("\nSecurity Issues:")
                    for issue in validation["security_issues"]:
                        print(f"  - [{issue['code']}] {issue['message']}")

                if validation["warnings"]:
                    print("\nWarnings:")
                    for warning in validation["warnings"][:10]:  # Show first 10
                        print(f"  - [{warning['code']}] {warning['message']}")

                if validation["metrics"]:
                    print("\nMetrics:")
                    for key, value in validation["metrics"].items():
                        print(f"  {key}: {value}")

            except Exception as e:
                print(f"✗ Validation failed: {e}")

    elif args.command == "sync":
        # Sync workflows with N8N
        async with manager.client as client:
            try:
                results = await client.sync_with_n8n(
                    sync_all=args.all, workflow_ids=args.workflows
                )

                print("Sync Results:")
                print(f"  Synced: {len(results['synced'])}")
                print(f"  Failed: {len(results['failed'])}")
                print(f"  Skipped: {len(results['skipped'])}")

                if results["synced"]:
                    print("\nSynced workflows:")
                    for wf in results["synced"]:
                        print(f"  ✓ {wf['name']}")

                if results["failed"]:
                    print("\nFailed workflows:")
                    for wf in results["failed"]:
                        print(f"  ✗ {wf['name']}: {wf['error']}")

                if results["skipped"] and args.all:
                    print("\nSkipped workflows:")
                    for wf in results["skipped"][:5]:  # Show first 5
                        print(f"  - {wf['name']}: {wf['reason']}")

            except Exception as e:
                print(f"✗ Sync failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
