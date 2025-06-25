"""
N8N Client SDK for ELF Teams

Provides interface for teams to execute and manage n8n workflows.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiohttp
from supabase import Client, create_client

from .exceptions import (
    N8NError,
    WorkflowExecutionError,
    WorkflowNotFoundError,
    WorkflowValidationError,
)
from .models import (
    ValidationStatus,
    WorkflowCategory,
    WorkflowExecution,
    WorkflowInfo,
    WorkflowSource,
    WorkflowSpec,
    WorkflowStatus,
    WorkflowTriggerType,
)
from .workflow_exporter import WorkflowExporter
from .workflow_importer import WorkflowImporter
from .workflow_validator import WorkflowValidator

logger = logging.getLogger(__name__)


class N8NClient:
    """SDK for teams to interact with n8n workflows"""

    def __init__(
        self,
        n8n_url: Optional[str] = None,
        n8n_api_key: Optional[str] = None,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ):
        """
        Initialize N8N client

        Args:
            n8n_url: N8N instance URL (defaults to cluster internal)
            n8n_api_key: N8N API key for authentication
            supabase_url: Supabase URL for registry
            supabase_key: Supabase key for registry
        """
        # N8N configuration
        self.n8n_url = n8n_url or os.getenv(
            "N8N_URL", "http://n8n.n8n.svc.cluster.local:5678"
        )
        self.n8n_api_key = n8n_api_key or os.getenv("N8N_API_KEY", "")

        # Supabase configuration
        supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        supabase_key = (
            supabase_key
            or os.getenv("SUPABASE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_SECRET_KEY")
        )

        if not supabase_url or not supabase_key:
            raise N8NError(
                "Supabase credentials not provided. Set SUPABASE_URL and SUPABASE_KEY (or SUPABASE_ANON_KEY) in environment"
            )

        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.session: Optional[aiohttp.ClientSession] = None

        # Initialize import/export/validation services
        self.importer = WorkflowImporter(self.supabase)
        self.exporter = WorkflowExporter(self.supabase)
        self.validator = WorkflowValidator()

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for N8N API requests"""
        headers = {"Content-Type": "application/json"}
        if self.n8n_api_key:
            headers["X-N8N-API-KEY"] = self.n8n_api_key
        return headers

    async def execute_workflow(
        self,
        workflow_name: str,
        data: Dict[str, Any],
        team_name: str,
        wait_for_completion: bool = True,
        timeout: int = 300,
    ) -> WorkflowExecution:
        """
        Execute a workflow by name

        Args:
            workflow_name: Name of the workflow to execute
            data: Input data for the workflow
            team_name: Name of the team triggering the workflow
            wait_for_completion: Whether to wait for workflow to complete
            timeout: Maximum time to wait in seconds

        Returns:
            WorkflowExecution object with results
        """
        # Find workflow in registry
        workflow_info = await self.get_workflow_info(workflow_name)
        if not workflow_info:
            raise WorkflowNotFoundError(workflow_name)

        if not workflow_info.is_active:
            raise WorkflowExecutionError(workflow_name, "Workflow is not active")

        # Create execution record
        execution_id = await self._create_execution_record(
            workflow_info, data, team_name
        )

        try:
            # Execute via webhook
            if workflow_info.trigger_type == WorkflowTriggerType.WEBHOOK:
                result = await self._execute_webhook(
                    workflow_info.webhook_url, data, execution_id
                )
            else:
                # For non-webhook workflows, use N8N API
                result = await self._execute_via_api(
                    workflow_info.n8n_workflow_id, data, execution_id
                )

            # Update execution record
            execution = await self._update_execution_record(
                execution_id, WorkflowStatus.SUCCESS, result
            )

            return execution

        except Exception as e:
            # Update execution record with failure
            execution = await self._update_execution_record(
                execution_id, WorkflowStatus.FAILED, error_message=str(e)
            )
            raise WorkflowExecutionError(workflow_name, str(e))

    async def get_workflow_info(self, workflow_name: str) -> Optional[WorkflowInfo]:
        """Get workflow information from registry"""
        try:
            response = (
                self.supabase.table("n8n_workflows")
                .select("*")
                .eq("name", workflow_name)
                .single()
                .execute()
            )

            if response.data:
                data = response.data
                return WorkflowInfo(
                    id=data["id"],
                    name=data["name"],
                    description=data["description"],
                    category=WorkflowCategory(data["category"]),
                    owner_team=data["owner_team"],
                    n8n_workflow_id=data["n8n_workflow_id"],
                    trigger_type=WorkflowTriggerType(data["trigger_type"]),
                    webhook_url=data.get("webhook_url"),
                    input_schema=data.get("input_schema", {}),
                    output_schema=data.get("output_schema", {}),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                    is_active=data["is_active"],
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching workflow info: {e}")
            return None

    async def list_workflows(
        self,
        owner_team: Optional[str] = None,
        category: Optional[WorkflowCategory] = None,
        active_only: bool = True,
    ) -> List[WorkflowInfo]:
        """List workflows with optional filters"""
        query = self.supabase.table("n8n_workflows").select("*")

        if owner_team:
            query = query.eq("owner_team", owner_team)
        if category:
            query = query.eq("category", category.value)
        if active_only:
            query = query.eq("is_active", True)

        response = query.execute()

        workflows = []
        for data in response.data:
            workflows.append(
                WorkflowInfo(
                    id=data["id"],
                    name=data["name"],
                    description=data["description"],
                    category=WorkflowCategory(data["category"]),
                    owner_team=data["owner_team"],
                    n8n_workflow_id=data["n8n_workflow_id"],
                    trigger_type=WorkflowTriggerType(data["trigger_type"]),
                    webhook_url=data.get("webhook_url"),
                    input_schema=data.get("input_schema", {}),
                    output_schema=data.get("output_schema", {}),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                    is_active=data["is_active"],
                )
            )

        return workflows

    async def get_execution_history(
        self,
        workflow_name: Optional[str] = None,
        team_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[WorkflowExecution]:
        """Get workflow execution history"""
        # For now, just get executions without the join
        query = self.supabase.table("workflow_executions").select("*")

        if workflow_name:
            # First get the workflow ID
            workflow = await self.get_workflow_info(workflow_name)
            if workflow:
                query = query.eq("workflow_id", workflow.id)
        if team_name:
            query = query.eq("triggered_by", team_name)

        query = query.order("started_at", desc=True).limit(limit)
        response = query.execute()

        executions = []

        # Get workflow names for the executions
        workflow_names = {}
        if response.data:
            workflow_ids = list(
                set(
                    data["workflow_id"] for data in response.data if data["workflow_id"]
                )
            )
            if workflow_ids:
                workflows = (
                    self.supabase.table("n8n_workflows")
                    .select("id, name")
                    .in_("id", workflow_ids)
                    .execute()
                )
                workflow_names = {w["id"]: w["name"] for w in workflows.data}

        for data in response.data:
            executions.append(
                WorkflowExecution(
                    id=data["id"],
                    workflow_id=data["workflow_id"],
                    workflow_name=workflow_names.get(data["workflow_id"], "Unknown"),
                    triggered_by=data["triggered_by"],
                    started_at=datetime.fromisoformat(data["started_at"]),
                    completed_at=datetime.fromisoformat(data["completed_at"])
                    if data["completed_at"]
                    else None,
                    status=WorkflowStatus(data["status"]),
                    input_data=data.get("input_data", {}),
                    output_data=data.get("output_data"),
                    error_message=data.get("error_message"),
                )
            )

        return executions

    async def register_workflow(self, spec: WorkflowSpec) -> WorkflowInfo:
        """Register a new workflow in the system"""
        # This will be implemented when we have the workflow factory
        raise NotImplementedError("Workflow registration coming in Phase 2")

    async def _execute_webhook(
        self, webhook_url: str, data: Dict[str, Any], execution_id: str
    ) -> Dict[str, Any]:
        """Execute workflow via webhook"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        # Add execution tracking
        payload = {**data, "_execution_id": execution_id}

        async with self.session.post(
            webhook_url, json=payload, headers=self._get_headers()
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise WorkflowExecutionError(
                    "webhook", f"HTTP {response.status}: {text}"
                )

            return await response.json()

    async def _execute_via_api(
        self, workflow_id: str, data: Dict[str, Any], execution_id: str
    ) -> Dict[str, Any]:
        """Execute workflow via N8N API"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.n8n_url}/api/v1/workflows/{workflow_id}/execute"

        async with self.session.post(
            url,
            json={"data": data, "execution_id": execution_id},
            headers=self._get_headers(),
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise WorkflowExecutionError("api", f"HTTP {response.status}: {text}")

            return await response.json()

    async def _create_execution_record(
        self, workflow_info: WorkflowInfo, input_data: Dict[str, Any], team_name: str
    ) -> str:
        """Create execution record in database"""
        import uuid

        execution_id = str(uuid.uuid4())

        self.supabase.table("workflow_executions").insert(
            {
                "id": execution_id,
                "workflow_id": workflow_info.id,
                "triggered_by": team_name,
                "started_at": datetime.utcnow().isoformat(),
                "status": WorkflowStatus.RUNNING.value,
                "input_data": input_data,
            }
        ).execute()

        return execution_id

    async def _update_execution_record(
        self,
        execution_id: str,
        status: WorkflowStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> WorkflowExecution:
        """Update execution record with results"""
        update_data = {
            "status": status.value,
            "completed_at": datetime.utcnow().isoformat(),
        }

        if output_data:
            update_data["output_data"] = output_data
        if error_message:
            update_data["error_message"] = error_message

        response = (
            self.supabase.table("workflow_executions")
            .update(update_data)
            .eq("id", execution_id)
            .execute()
        )

        # Fetch complete record
        result = (
            self.supabase.table("workflow_executions")
            .select("*")
            .eq("id", execution_id)
            .single()
            .execute()
        )

        data = result.data

        # Get workflow name
        workflow_result = (
            self.supabase.table("n8n_workflows")
            .select("name")
            .eq("id", data["workflow_id"])
            .single()
            .execute()
        )
        workflow_name = (
            workflow_result.data["name"] if workflow_result.data else "Unknown"
        )

        return WorkflowExecution(
            id=data["id"],
            workflow_id=data["workflow_id"],
            workflow_name=workflow_name,
            triggered_by=data["triggered_by"],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data["completed_at"]
            else None,
            status=WorkflowStatus(data["status"]),
            input_data=data.get("input_data", {}),
            output_data=data.get("output_data"),
            error_message=data.get("error_message"),
        )

    # Import/Export Methods

    def import_workflow(
        self,
        workflow_json: Union[Dict[str, Any], str],
        name: str,
        category: Union[WorkflowCategory, str],
        owner_team: str,
        imported_by: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: Union[WorkflowSource, str] = WorkflowSource.N8N_EXPORT,
    ) -> Dict[str, Any]:
        """
        Import a workflow into the database

        Args:
            workflow_json: N8N workflow JSON (dict or JSON string)
            name: Workflow name
            category: Workflow category
            owner_team: Team that owns this workflow
            imported_by: User/system importing the workflow
            description: Optional description
            tags: Optional tags
            source: Source of the workflow

        Returns:
            Created workflow record
        """
        # Convert string enums to enum types
        if isinstance(category, str):
            category = WorkflowCategory.from_string(category)
        if isinstance(source, str):
            source = WorkflowSource(source)

        return self.importer.import_workflow(
            workflow_json=workflow_json,
            name=name,
            category=category,
            owner_team=owner_team,
            imported_by=imported_by,
            description=description,
            tags=tags,
            source=source,
        )

    def import_from_file(self, file_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
        """
        Import workflow from a JSON file

        Args:
            file_path: Path to workflow JSON file
            **kwargs: Additional arguments passed to import_workflow

        Returns:
            Created workflow record
        """
        from pathlib import Path

        return self.importer.import_from_file(file_path, **kwargs)

    def export_workflow(
        self,
        workflow_id: Optional[str] = None,
        workflow_slug: Optional[str] = None,
        version: Optional[int] = None,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Export a workflow to N8N format

        Args:
            workflow_id: Workflow ID (provide either this or slug)
            workflow_slug: Workflow slug (provide either this or ID)
            version: Specific version to export (latest if not specified)
            include_metadata: Include export metadata

        Returns:
            Workflow in N8N format with optional metadata
        """
        return self.exporter.export_workflow(
            workflow_id=workflow_id,
            workflow_slug=workflow_slug,
            version=version,
            include_metadata=include_metadata,
        )

    def export_to_file(
        self,
        workflow_id: Optional[str] = None,
        workflow_slug: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
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
        from pathlib import Path

        return self.exporter.export_to_file(
            workflow_id=workflow_id,
            workflow_slug=workflow_slug,
            output_path=output_path,
            version=version,
            include_metadata=include_metadata,
        )

    def validate_workflow(
        self,
        workflow_json: Dict[str, Any],
        owner_team: Optional[str] = None,
        check_permissions: bool = True,
        deep_validation: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate a workflow

        Args:
            workflow_json: N8N workflow JSON
            owner_team: Team that will own this workflow
            check_permissions: Check team permissions for resources
            deep_validation: Perform deep analysis (slower but more thorough)

        Returns:
            Validation result dictionary
        """
        result = self.validator.validate_workflow(
            workflow_json=workflow_json,
            owner_team=owner_team,
            check_permissions=check_permissions,
            deep_validation=deep_validation,
        )
        return result.to_dict()

    async def import_workflow(
        self,
        source: str,
        source_type: str = "json",  # json, file, url
        owner_team: str = "default",
        category: str = "imported",
        validate: bool = True,
        process: bool = True,
        auto_fix: bool = False,
    ) -> Dict[str, Any]:
        """
        Import a workflow from various sources

        Args:
            source: The workflow source (JSON string, file path, or URL)
            source_type: Type of source - json, file, or url
            owner_team: Team that will own this workflow
            category: Category to assign to the workflow
            validate: Whether to validate the workflow
            process: Whether to process the workflow for compatibility
            auto_fix: Whether to auto-fix common issues

        Returns:
            Dictionary with workflow_id and validation report
        """
        workflow_id, validation_report = await self.importer.import_workflow(
            source=source,
            source_type=source_type,
            owner_team=owner_team,
            category=category,
            validate=validate,
            process=process,
            auto_fix=auto_fix,
        )

        return {
            "workflow_id": workflow_id,
            "validation_report": validation_report.__dict__
            if validation_report
            else None,
            "success": workflow_id is not None,
        }

    async def sync_with_n8n(
        self, sync_all: bool = False, workflow_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sync workflows between database and N8N instance

        Args:
            sync_all: Sync all workflows
            workflow_ids: Specific workflow IDs to sync

        Returns:
            Sync results
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        results = {"synced": [], "failed": [], "skipped": []}

        # Get workflows to sync
        query = self.supabase.table("workflow_registry").select("*")

        if not sync_all and workflow_ids:
            query = query.in_("id", workflow_ids)
        elif not sync_all:
            # Only sync active workflows by default
            query = query.in_("status", ["running", "deployed"])

        workflows = query.execute()

        for workflow in workflows.data:
            try:
                # Skip if no N8N ID
                if not workflow.get("n8n_workflow_id"):
                    results["skipped"].append(
                        {
                            "id": workflow["id"],
                            "name": workflow["name"],
                            "reason": "No N8N workflow ID",
                        }
                    )
                    continue

                # Fetch workflow from N8N
                url = f"{self.n8n_url}/api/v1/workflows/{workflow['n8n_workflow_id']}"

                async with self.session.get(
                    url, headers=self._get_headers()
                ) as response:
                    if response.status == 200:
                        n8n_workflow = await response.json()

                        # Update workflow in database
                        self.importer.update_workflow(
                            workflow_id=workflow["id"],
                            workflow_json=n8n_workflow,
                            change_summary="Synced from N8N",
                            changed_by="sync_process",
                        )

                        results["synced"].append(
                            {"id": workflow["id"], "name": workflow["name"]}
                        )
                    else:
                        results["failed"].append(
                            {
                                "id": workflow["id"],
                                "name": workflow["name"],
                                "error": f"N8N returned status {response.status}",
                            }
                        )

            except Exception as e:
                results["failed"].append(
                    {"id": workflow["id"], "name": workflow["name"], "error": str(e)}
                )

        return results
