"""
N8N Workflow Importer

Handles importing workflows from various sources with validation and processing.
"""

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from elf_automations.shared.n8n.workflow_validator import (
    ValidationLevel,
    ValidationReport,
    ValidationStatus,
    WorkflowValidator,
)
from elf_automations.shared.utils.llm_factory import LLMFactory
from supabase import Client


class WorkflowImporter:
    """Imports N8N workflows with validation and processing"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.validator = WorkflowValidator()
        self.llm = LLMFactory.create_llm(
            preferred_provider="anthropic",
            preferred_model="claude-3-sonnet-20240229",
            temperature=0.3,
            enable_fallback=True,
        )

    async def import_workflow(
        self,
        source: str,
        source_type: str = "json",  # json, file, url
        owner_team: str = "default",
        category: str = "imported",
        validate: bool = True,
        process: bool = True,
        auto_fix: bool = False,
    ) -> Tuple[Optional[str], ValidationReport]:
        """Import a workflow from various sources"""

        # 1. Load workflow
        workflow_data = await self._load_workflow(source, source_type)
        if not workflow_data:
            return None, self._create_error_report("Failed to load workflow")

        # 2. Validate if requested
        validation_report = None
        if validate:
            validation_report = self.validator.validate(
                workflow_data, ValidationLevel.FULL
            )

            if validation_report.status == ValidationStatus.FAILED and not auto_fix:
                return None, validation_report

        # 3. Process workflow if requested
        processed_workflow = workflow_data
        if process:
            processed_workflow = await self._process_workflow(
                workflow_data, validation_report, auto_fix
            )

        # 4. Extract metadata
        metadata = self._extract_metadata(processed_workflow)

        # 5. Generate unique workflow ID
        workflow_id = f"imported_{uuid.uuid4().hex[:8]}"

        # 6. Store in database
        try:
            # Insert main workflow record
            workflow_record = {
                "workflow_id": workflow_id,
                "name": processed_workflow.get("name", "Imported Workflow"),
                "description": metadata.get(
                    "ai_description", processed_workflow.get("description", "")
                ),
                "category": category,
                "tags": metadata.get("tags", []),
                "owner_team": owner_team,
                "source": "imported",
                "source_url": source if source_type == "url" else None,
                "status": "validated"
                if validation_report
                and validation_report.status != ValidationStatus.FAILED
                else "draft",
                "validation_status": validation_report.status.value
                if validation_report
                else "pending",
                "last_validation": datetime.utcnow().isoformat(),
                "node_types": metadata.get("node_types", []),
                "integrations": metadata.get("integrations", []),
                "complexity_score": metadata.get("complexity_score", 5),
                "estimated_cost_per_run": validation_report.estimated_cost
                if validation_report
                else 0.0,
                "created_by": "workflow_importer",
            }

            workflow_result = (
                self.supabase.table("workflows").insert(workflow_record).execute()
            )

            if not workflow_result.data:
                return None, self._create_error_report(
                    "Failed to create workflow record"
                )

            workflow_uuid = workflow_result.data[0]["id"]

            # Insert workflow version
            version_record = {
                "workflow_id": workflow_uuid,
                "workflow_json": workflow_data,  # Original
                "processed_json": processed_workflow,  # Processed version
                "validation_status": validation_report.status.value
                if validation_report
                else "pending",
                "validation_report": self._serialize_validation_report(
                    validation_report
                )
                if validation_report
                else None,
                "created_by": "workflow_importer",
            }

            self.supabase.table("workflow_versions").insert(version_record).execute()

            # Insert metadata
            metadata_record = {
                "workflow_id": workflow_uuid,
                "trigger_types": metadata.get("trigger_types", []),
                "input_sources": metadata.get("input_sources", []),
                "output_destinations": metadata.get("output_destinations", []),
                "required_credentials": metadata.get("required_credentials", {}),
                "environment_variables": metadata.get("environment_variables", []),
                "webhook_urls": metadata.get("webhook_urls", []),
                "ai_generated_description": metadata.get("ai_description"),
                "ai_suggested_improvements": metadata.get("ai_improvements", {}),
                "ai_detected_patterns": metadata.get("detected_patterns", []),
            }

            self.supabase.table("workflow_metadata").insert(metadata_record).execute()

            # Log the import
            import_log = {
                "workflow_id": workflow_uuid,
                "operation": "import",
                "operation_status": "success",
                "source_format": source_type,
                "source_data": source[:255] if source_type != "json" else "inline_json",
                "original_json": workflow_data,
                "performed_by": "workflow_importer",
            }

            self.supabase.table("workflow_import_export_log").insert(
                import_log
            ).execute()

            return workflow_uuid, validation_report or self._create_success_report()

        except Exception as e:
            return None, self._create_error_report(f"Database error: {str(e)}")

    async def _load_workflow(
        self, source: str, source_type: str
    ) -> Optional[Dict[str, Any]]:
        """Load workflow from various sources"""

        try:
            if source_type == "json":
                return json.loads(source)

            elif source_type == "file":
                with open(source, "r") as f:
                    return json.load(f)

            elif source_type == "url":
                async with httpx.AsyncClient() as client:
                    response = await client.get(source, timeout=30.0)
                    response.raise_for_status()
                    return response.json()

            else:
                raise ValueError(f"Unknown source type: {source_type}")

        except Exception as e:
            print(f"Error loading workflow: {e}")
            return None

    async def _process_workflow(
        self,
        workflow: Dict[str, Any],
        validation_report: Optional[ValidationReport],
        auto_fix: bool,
    ) -> Dict[str, Any]:
        """Process workflow to make it compatible with our environment"""

        processed = workflow.copy()

        # 1. Sanitize credentials
        processed = self._sanitize_credentials(processed)

        # 2. Update webhook URLs
        processed = self._update_webhook_urls(processed)

        # 3. Fix common issues if auto_fix is enabled
        if auto_fix and validation_report:
            processed = self._auto_fix_issues(processed, validation_report)

        # 4. Add our environment variables
        processed = self._add_environment_config(processed)

        # 5. Use AI to improve the workflow
        processed = await self._ai_enhance_workflow(processed)

        return processed

    def _sanitize_credentials(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Remove hardcoded credentials and replace with placeholders"""

        workflow_str = json.dumps(workflow)

        # Pattern replacements
        replacements = {
            r'(api[_-]?key|apikey)[\s]*[:=][\s]*["\']?([a-zA-Z0-9\-_]{20,})["\']?': r"\1={{$credentials.\1}}",
            r'(password|passwd|pwd)[\s]*[:=][\s]*["\']?([^\s"\']+)["\']?': r"\1={{$credentials.password}}",
            r'(token|access[_-]?token)[\s]*[:=][\s]*["\']?([a-zA-Z0-9\-_]{20,})["\']?': r"\1={{$credentials.token}}",
            r"https?://[^:]+:[^@]+@": "https://{{$credentials.username}}:{{$credentials.password}}@",
        }

        for pattern, replacement in replacements.items():
            workflow_str = re.sub(pattern, replacement, workflow_str, flags=re.I)

        return json.loads(workflow_str)

    def _update_webhook_urls(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Update webhook URLs to use our domain"""

        for node in workflow.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.webhook":
                params = node.get("parameters", {})
                if "path" in params:
                    # Ensure path starts with /
                    path = params["path"]
                    if not path.startswith("/"):
                        path = f"/{path}"
                    params["path"] = path

                # Add authentication if missing
                if "authentication" not in params:
                    params["authentication"] = "headerAuth"
                    params["httpHeaderAuth"] = {
                        "name": "X-Webhook-Token",
                        "value": "={{$credentials.webhookToken}}",
                    }

        return workflow

    def _auto_fix_issues(
        self, workflow: Dict[str, Any], validation_report: ValidationReport
    ) -> Dict[str, Any]:
        """Automatically fix common issues"""

        # Add missing name
        if not workflow.get("name") or workflow.get("name") == "My workflow":
            workflow[
                "name"
            ] = f"Imported Workflow {datetime.now().strftime('%Y-%m-%d')}"

        # Add error workflow setting
        if "settings" not in workflow:
            workflow["settings"] = {}

        if "errorWorkflow" not in workflow["settings"]:
            workflow["settings"]["errorWorkflow"] = "error-handler"

        # Enable execution data saving
        workflow["settings"]["saveDataSuccessExecution"] = "all"
        workflow["settings"]["saveManualExecutions"] = True

        return workflow

    def _add_environment_config(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Add our environment-specific configuration"""

        # Add environment tags
        if "tags" not in workflow:
            workflow["tags"] = []

        workflow["tags"].extend(["imported", "needs-review"])

        # Update settings for our environment
        if "settings" not in workflow:
            workflow["settings"] = {}

        workflow["settings"]["timezone"] = "America/New_York"
        workflow["settings"]["executionTimeout"] = 300  # 5 minutes default

        return workflow

    async def _ai_enhance_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to enhance and document the workflow"""

        prompt = f"""Analyze this N8N workflow and provide enhancements:

Workflow: {json.dumps(workflow, indent=2)}

Please provide:
1. A clear, concise description of what this workflow does
2. Suggested improvements (but don't modify the workflow)
3. Detected patterns or use cases
4. Any security or performance concerns

Return as JSON:
{{
    "description": "clear description",
    "improvements": ["improvement1", "improvement2"],
    "patterns": ["pattern1", "pattern2"],
    "concerns": ["concern1", "concern2"]
}}"""

        try:
            response = self.llm.invoke(prompt)
            enhancements = json.loads(response.content)

            # Add AI-generated description if none exists
            if not workflow.get("description"):
                workflow["description"] = enhancements.get("description", "")

            # Store AI insights in workflow metadata (not in the workflow itself)
            if "meta" not in workflow:
                workflow["meta"] = {}

            workflow["meta"]["ai_analysis"] = {
                "generated_at": datetime.utcnow().isoformat(),
                "improvements": enhancements.get("improvements", []),
                "patterns": enhancements.get("patterns", []),
                "concerns": enhancements.get("concerns", []),
            }

        except Exception as e:
            print(f"AI enhancement failed: {e}")

        return workflow

    def _extract_metadata(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Extract searchable metadata from workflow"""

        metadata = {
            "node_types": [],
            "integrations": [],
            "trigger_types": [],
            "input_sources": [],
            "output_destinations": [],
            "required_credentials": {},
            "environment_variables": [],
            "webhook_urls": [],
            "tags": [],
            "complexity_score": 5,
            "detected_patterns": [],
        }

        # Extract node information
        for node in workflow.get("nodes", []):
            node_type = node.get("type", "")
            metadata["node_types"].append(node_type)

            # Detect integrations
            if "slack" in node_type.lower():
                metadata["integrations"].append("slack")
            elif "gmail" in node_type.lower():
                metadata["integrations"].append("gmail")
            elif "twilio" in node_type.lower():
                metadata["integrations"].append("twilio")
            # ... add more integrations

            # Detect triggers
            if "trigger" in node_type.lower():
                metadata["trigger_types"].append(node_type)

            # Extract webhook URLs
            if node.get("type") == "n8n-nodes-base.webhook":
                path = node.get("parameters", {}).get("path")
                if path:
                    metadata["webhook_urls"].append(path)

        # Extract from AI analysis if available
        ai_analysis = workflow.get("meta", {}).get("ai_analysis", {})
        metadata["ai_description"] = workflow.get("description", "")
        metadata["ai_improvements"] = ai_analysis.get("improvements", [])
        metadata["detected_patterns"] = ai_analysis.get("patterns", [])

        # Calculate complexity
        node_count = len(workflow.get("nodes", []))
        if node_count < 5:
            metadata["complexity_score"] = 1
        elif node_count < 10:
            metadata["complexity_score"] = 3
        elif node_count < 20:
            metadata["complexity_score"] = 5
        elif node_count < 30:
            metadata["complexity_score"] = 7
        else:
            metadata["complexity_score"] = 9

        # Generate tags
        metadata["tags"] = list(set(metadata["integrations"] + ["imported"]))

        return metadata

    def _serialize_validation_report(self, report: ValidationReport) -> Dict[str, Any]:
        """Serialize validation report for storage"""

        return {
            "status": report.status.value,
            "errors": [
                {
                    "field": e.field,
                    "message": e.message,
                    "severity": e.severity,
                    "suggestion": e.suggestion,
                }
                for e in report.errors
            ],
            "warnings": [
                {"field": w.field, "message": w.message, "suggestion": w.suggestion}
                for w in report.warnings
            ],
            "suggestions": report.suggestions,
            "security_issues": report.security_issues,
            "missing_nodes": report.missing_nodes,
            "credential_requirements": [
                {
                    "type": cr.type,
                    "name": cr.name,
                    "node_id": cr.node_id,
                    "is_available": cr.is_available,
                    "suggested_mapping": cr.suggested_mapping,
                }
                for cr in report.credential_requirements
            ],
            "estimated_cost": report.estimated_cost,
            "complexity_score": report.complexity_score,
            "compatibility_score": report.compatibility_score,
            "validated_at": report.validated_at.isoformat(),
        }

    def _create_error_report(self, message: str) -> ValidationReport:
        """Create an error validation report"""

        from elf_automations.shared.n8n.workflow_validator import ValidationError

        return ValidationReport(
            status=ValidationStatus.FAILED,
            errors=[ValidationError(field="import", message=message)],
            warnings=[],
            suggestions=[],
            is_valid_schema=False,
            security_issues=[],
            missing_nodes=[],
            credential_requirements=[],
            estimated_cost=0.0,
            complexity_score=0,
            compatibility_score=0.0,
            validated_at=datetime.utcnow(),
            validation_level=ValidationLevel.BASIC,
        )

    def _create_success_report(self) -> ValidationReport:
        """Create a success validation report"""

        return ValidationReport(
            status=ValidationStatus.PASSED,
            errors=[],
            warnings=[],
            suggestions=[],
            is_valid_schema=True,
            security_issues=[],
            missing_nodes=[],
            credential_requirements=[],
            estimated_cost=0.0,
            complexity_score=0,
            compatibility_score=100.0,
            validated_at=datetime.utcnow(),
            validation_level=ValidationLevel.BASIC,
        )

    async def import_batch(
        self,
        sources: List[Tuple[str, str]],  # [(source, source_type), ...]
        owner_team: str = "default",
        category: str = "imported",
    ) -> List[Tuple[Optional[str], ValidationReport]]:
        """Import multiple workflows in batch"""

        results = []

        for source, source_type in sources:
            result = await self.import_workflow(
                source=source,
                source_type=source_type,
                owner_team=owner_team,
                category=category,
            )
            results.append(result)

        return results
