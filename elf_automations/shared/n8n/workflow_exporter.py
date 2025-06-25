"""
N8N Workflow Exporter

Handles exporting workflows from the database to N8N format.
Supports single and bulk exports, versioning, and format conversion.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from zipfile import ZipFile

from supabase import Client

from .exceptions import N8NError, WorkflowNotFoundError
from .models import WorkflowStatus

logger = logging.getLogger(__name__)


class WorkflowExporter:
    """Export workflows from database to N8N format"""

    def __init__(self, supabase_client: Client):
        """
        Initialize workflow exporter

        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client

    def export_workflow(
        self,
        workflow_id: Optional[str] = None,
        workflow_slug: Optional[str] = None,
        version: Optional[int] = None,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Export a single workflow to N8N format

        Args:
            workflow_id: Workflow ID (provide either this or slug)
            workflow_slug: Workflow slug (provide either this or ID)
            version: Specific version to export (latest if not specified)
            include_metadata: Include export metadata

        Returns:
            Workflow in N8N format with optional metadata
        """
        if not workflow_id and not workflow_slug:
            raise ValueError("Must provide either workflow_id or workflow_slug")

        # Fetch workflow
        query = self.supabase.table("workflow_registry").select("*")

        if workflow_id:
            query = query.eq("id", workflow_id)
        else:
            query = query.eq("slug", workflow_slug)

        result = query.single().execute()

        if not result.data:
            raise WorkflowNotFoundError(
                f"Workflow not found: {workflow_id or workflow_slug}"
            )

        workflow = result.data

        # Get specific version if requested
        if version is not None:
            version_result = (
                self.supabase.table("workflow_versions")
                .select("*")
                .eq("workflow_id", workflow["id"])
                .eq("version_number", version)
                .single()
                .execute()
            )

            if not version_result.data:
                raise N8NError(
                    f"Version {version} not found for workflow {workflow['name']}"
                )

            workflow_json = version_result.data["n8n_workflow_json"]
        else:
            workflow_json = workflow["n8n_workflow_json"]

        # Ensure workflow has been imported (has actual JSON)
        if not workflow_json or workflow_json == {}:
            raise N8NError(
                f"Workflow {workflow['name']} has no workflow definition. It may need to be imported from N8N first."
            )

        # Add/update workflow metadata
        workflow_json["name"] = workflow["name"]
        workflow_json["id"] = workflow.get(
            "n8n_workflow_id"
        )  # Preserve N8N ID if exists

        # Prepare export
        if include_metadata:
            export_data = {
                "workflow": workflow_json,
                "metadata": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "workflow_id": workflow["id"],
                    "slug": workflow["slug"],
                    "version": version or workflow["version"],
                    "category": workflow["category"],
                    "owner_team": workflow["owner_team"],
                    "tags": workflow.get("tags", []),
                    "status": workflow["status"],
                    "description": workflow.get("description"),
                },
            }
        else:
            export_data = workflow_json

        # Log export
        log_data = {
            "operation_type": "export",
            "workflow_id": workflow["id"],
            "status": "completed",
            "initiated_by": "api",
            "metadata": {
                "version": version or workflow["version"],
                "include_metadata": include_metadata,
            },
        }

        self.supabase.table("workflow_import_export_log").insert(log_data).execute()

        return export_data

    def export_to_file(
        self,
        workflow_id: Optional[str] = None,
        workflow_slug: Optional[str] = None,
        output_path: Union[str, Path] = None,
        version: Optional[int] = None,
        include_metadata: bool = True,
    ) -> Path:
        """
        Export workflow to a JSON file

        Args:
            workflow_id: Workflow ID
            workflow_slug: Workflow slug
            output_path: Output file path (auto-generated if not provided)
            version: Specific version to export
            include_metadata: Include export metadata

        Returns:
            Path to exported file
        """
        # Export workflow
        export_data = self.export_workflow(
            workflow_id=workflow_id,
            workflow_slug=workflow_slug,
            version=version,
            include_metadata=include_metadata,
        )

        # Determine output path
        if output_path is None:
            workflow_name = export_data.get("metadata", {}).get("slug") or "workflow"
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"{workflow_name}_{timestamp}.json")
        else:
            output_path = Path(output_path)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported workflow to {output_path}")

        return output_path

    def export_batch(
        self,
        workflow_ids: Optional[List[str]] = None,
        category: Optional[str] = None,
        owner_team: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        tags: Optional[List[str]] = None,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Export multiple workflows based on filters

        Args:
            workflow_ids: Specific workflow IDs to export
            category: Filter by category
            owner_team: Filter by owner team
            status: Filter by status
            tags: Filter by tags (any match)
            include_metadata: Include export metadata

        Returns:
            List of exported workflows
        """
        # Build query
        query = self.supabase.table("workflow_registry").select("id")

        if workflow_ids:
            query = query.in_("id", workflow_ids)
        if category:
            query = query.eq("category", category)
        if owner_team:
            query = query.eq("owner_team", owner_team)
        if status:
            query = query.eq("status", status.value)
        if tags:
            query = query.contains("tags", tags)

        # Execute query
        result = query.execute()

        if not result.data:
            logger.warning("No workflows found matching filters")
            return []

        # Export each workflow
        exported_workflows = []

        for workflow in result.data:
            try:
                export_data = self.export_workflow(
                    workflow_id=workflow["id"], include_metadata=include_metadata
                )
                exported_workflows.append(export_data)
            except Exception as e:
                logger.error(f"Failed to export workflow {workflow['id']}: {e}")

        logger.info(f"Exported {len(exported_workflows)} workflows")

        return exported_workflows

    def export_to_archive(
        self,
        output_path: Union[str, Path],
        workflow_ids: Optional[List[str]] = None,
        category: Optional[str] = None,
        owner_team: Optional[str] = None,
        include_templates: bool = False,
    ) -> Path:
        """
        Export workflows to a ZIP archive

        Args:
            output_path: Output ZIP file path
            workflow_ids: Specific workflows to export
            category: Filter by category
            owner_team: Filter by owner team
            include_templates: Also export workflow templates

        Returns:
            Path to created archive
        """
        output_path = Path(output_path)

        # Ensure .zip extension
        if output_path.suffix != ".zip":
            output_path = output_path.with_suffix(".zip")

        # Export workflows
        workflows = self.export_batch(
            workflow_ids=workflow_ids,
            category=category,
            owner_team=owner_team,
            include_metadata=True,
        )

        # Create archive
        with ZipFile(output_path, "w") as zipf:
            # Add manifest
            manifest = {
                "export_date": datetime.utcnow().isoformat(),
                "workflow_count": len(workflows),
                "exporter_version": "1.0.0",
            }

            zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

            # Add workflows
            for i, workflow_data in enumerate(workflows):
                metadata = workflow_data.get("metadata", {})
                filename = f"workflows/{metadata.get('slug', f'workflow_{i}')}.json"
                zipf.writestr(filename, json.dumps(workflow_data, indent=2))

            # Add templates if requested
            if include_templates:
                templates_result = (
                    self.supabase.table("workflow_templates").select("*").execute()
                )

                if templates_result.data:
                    for template in templates_result.data:
                        filename = f"templates/{template['template_slug']}.json"
                        zipf.writestr(filename, json.dumps(template, indent=2))

                    manifest["template_count"] = len(templates_result.data)

            # Update manifest
            zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

        logger.info(f"Created workflow archive: {output_path}")

        return output_path

    def export_as_template(
        self,
        workflow_id: str,
        template_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        created_by: str = "system",
    ) -> Dict[str, Any]:
        """
        Export a workflow as a reusable template

        Args:
            workflow_id: Workflow to convert to template
            template_name: Name for the template
            parameters: Parameter definitions for the template
            created_by: User creating the template

        Returns:
            Created template record
        """
        # Get workflow
        workflow_result = (
            self.supabase.table("workflow_registry")
            .select("*")
            .eq("id", workflow_id)
            .single()
            .execute()
        )

        if not workflow_result.data:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")

        workflow = workflow_result.data
        workflow_json = workflow["n8n_workflow_json"]

        if not workflow_json or workflow_json == {}:
            raise N8NError("Cannot create template from workflow without definition")

        # Generate template slug
        template_slug = template_name.lower().replace(" ", "-").replace("_", "-")
        template_slug = "".join(c for c in template_slug if c.isalnum() or c == "-")

        # Ensure unique slug
        existing = (
            self.supabase.table("workflow_templates")
            .select("template_slug")
            .eq("template_slug", template_slug)
            .execute()
        )
        if existing.data:
            import uuid

            template_slug = f"{template_slug}-{str(uuid.uuid4())[:8]}"

        # TODO: Parameterize the workflow JSON based on provided parameters
        # For now, just use as-is
        template_json = workflow_json.copy()

        # Create template
        template_data = {
            "template_name": template_name,
            "template_slug": template_slug,
            "category": workflow["category"],
            "description": f"Template based on {workflow['name']}",
            "n8n_template_json": template_json,
            "parameters": parameters or {},
            "required_inputs": workflow.get("input_schema", {}),
            "expected_outputs": workflow.get("output_schema", {}),
            "tags": workflow.get("tags", []),
            "created_by": created_by,
        }

        result = (
            self.supabase.table("workflow_templates").insert(template_data).execute()
        )

        if not result.data:
            raise N8NError("Failed to create template")

        logger.info(
            f"Created template '{template_name}' from workflow {workflow['name']}"
        )

        return result.data[0]

    def get_export_formats(self) -> List[str]:
        """Get list of supported export formats"""
        return ["json", "n8n", "archive", "template"]

    def convert_format(
        self, workflow_data: Dict[str, Any], target_format: str
    ) -> Union[Dict[str, Any], str]:
        """
        Convert workflow to different formats

        Args:
            workflow_data: Workflow data (with or without metadata)
            target_format: Target format (json, n8n, etc.)

        Returns:
            Converted workflow data
        """
        if target_format == "json":
            return workflow_data

        elif target_format == "n8n":
            # Extract just the workflow JSON for N8N
            if "workflow" in workflow_data:
                return workflow_data["workflow"]
            return workflow_data

        elif target_format == "markdown":
            # Convert to documentation format
            workflow = workflow_data.get("workflow", workflow_data)
            metadata = workflow_data.get("metadata", {})

            md = f"# {workflow.get('name', 'Workflow')}\n\n"

            if metadata.get("description"):
                md += f"{metadata['description']}\n\n"

            md += "## Details\n\n"
            md += f"- **Category**: {metadata.get('category', 'N/A')}\n"
            md += f"- **Owner Team**: {metadata.get('owner_team', 'N/A')}\n"
            md += f"- **Status**: {metadata.get('status', 'N/A')}\n"

            if metadata.get("tags"):
                md += f"- **Tags**: {', '.join(metadata['tags'])}\n"

            md += f"\n## Nodes\n\n"

            nodes = workflow.get("nodes", [])
            for node in nodes:
                md += f"- **{node.get('name', 'Unnamed')}** ({node.get('type', 'Unknown')})\n"

            return md

        else:
            raise ValueError(f"Unsupported format: {target_format}")
