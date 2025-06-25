"""
N8N Workflow Validator

Comprehensive validation for imported workflows including security, compatibility, and best practices.
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from elf_automations.shared.n8n.workflow_analyzer import IssueSeverity, WorkflowAnalyzer


class ValidationLevel(Enum):
    """Validation levels"""

    BASIC = "basic"  # Schema and structure
    SECURITY = "security"  # Security issues
    COMPATIBILITY = "compatibility"  # Node and credential compatibility
    PERFORMANCE = "performance"  # Performance and cost
    FULL = "full"  # All validations


class ValidationStatus(Enum):
    """Overall validation status"""

    PASSED = "passed"
    WARNINGS = "warnings"
    FAILED = "failed"


@dataclass
class ValidationError:
    """Represents a validation error"""

    field: str
    message: str
    severity: str = "error"
    suggestion: Optional[str] = None


@dataclass
class ValidationWarning:
    """Represents a validation warning"""

    field: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class CredentialRequirement:
    """Represents a required credential"""

    type: str
    name: str
    node_id: str
    is_available: bool = False
    suggested_mapping: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report"""

    status: ValidationStatus
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    suggestions: List[str]

    # Specific validations
    is_valid_schema: bool
    security_issues: List[Dict[str, Any]]
    missing_nodes: List[str]
    credential_requirements: List[CredentialRequirement]

    # Metrics
    estimated_cost: float
    complexity_score: int
    compatibility_score: float  # 0-100

    # Metadata
    validated_at: datetime
    validation_level: ValidationLevel


class WorkflowValidator:
    """Validates N8N workflows for import"""

    def __init__(
        self,
        available_nodes: Optional[Set[str]] = None,
        available_credentials: Optional[Dict[str, str]] = None,
    ):
        self.analyzer = WorkflowAnalyzer()

        # Default available nodes (extend as needed)
        self.available_nodes = available_nodes or {
            "n8n-nodes-base.webhook",
            "n8n-nodes-base.scheduleTrigger",
            "n8n-nodes-base.httpRequest",
            "n8n-nodes-base.postgres",
            "n8n-nodes-base.supabase",
            "n8n-nodes-base.code",
            "n8n-nodes-base.if",
            "n8n-nodes-base.switch",
            "n8n-nodes-base.merge",
            "n8n-nodes-base.slack",
            "n8n-nodes-base.emailSend",
            "n8n-nodes-base.gmail",
            "n8n-nodes-base.twilio",
            "n8n-nodes-base.googleSheets",
            "@n8n/n8n-nodes-langchain.agent",
            "@n8n/n8n-nodes-langchain.vectorStore",
            "@n8n/n8n-nodes-langchain.memory",
            "@n8n/n8n-nodes-langchain.documentLoader",
            "@n8n/n8n-nodes-langchain.textSplitter",
        }

        # Available credential types
        self.available_credentials = available_credentials or {
            "slackApi": "slack_api",
            "gmailOAuth2": "gmail_oauth",
            "postgresDb": "postgres_db",
            "supabaseApi": "supabase_api",
            "openAiApi": "openai_api",
            "anthropicApi": "anthropic_api",
        }

        # Patterns for detecting secrets
        self.secret_patterns = {
            "api_key": re.compile(
                r'(api[_-]?key|apikey)[\s]*[:=][\s]*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
                re.I,
            ),
            "password": re.compile(
                r'(password|passwd|pwd)[\s]*[:=][\s]*["\']?([^\s"\']+)["\']?', re.I
            ),
            "token": re.compile(
                r'(token|access[_-]?token)[\s]*[:=][\s]*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
                re.I,
            ),
            "secret": re.compile(
                r'(secret|private[_-]?key)[\s]*[:=][\s]*["\']?([^\s"\']+)["\']?', re.I
            ),
            "url_with_auth": re.compile(r"https?://[^:]+:[^@]+@[^\s]+", re.I),
        }

    def validate(
        self, workflow: Dict[str, Any], level: ValidationLevel = ValidationLevel.FULL
    ) -> ValidationReport:
        """Validate a workflow at the specified level"""

        errors = []
        warnings = []
        suggestions = []

        # Basic validation
        is_valid_schema = self._validate_schema(workflow, errors)

        # Security validation
        security_issues = []
        if level in [ValidationLevel.SECURITY, ValidationLevel.FULL]:
            security_issues = self._validate_security(workflow, errors, warnings)

        # Compatibility validation
        missing_nodes = []
        credential_requirements = []
        compatibility_score = 100.0

        if level in [ValidationLevel.COMPATIBILITY, ValidationLevel.FULL]:
            missing_nodes = self._validate_nodes(workflow, errors)
            credential_requirements = self._extract_credentials(workflow)
            compatibility_score = self._calculate_compatibility_score(
                missing_nodes, credential_requirements
            )

        # Performance validation
        estimated_cost = 0.0
        complexity_score = 0

        if level in [ValidationLevel.PERFORMANCE, ValidationLevel.FULL]:
            # Use analyzer for performance metrics
            issues, metrics = self.analyzer.analyze_workflow(workflow)
            estimated_cost = metrics.estimated_cost_per_run
            complexity_score = int(metrics.complexity_score)

            # Add performance warnings
            for issue in issues:
                if issue.severity == IssueSeverity.HIGH:
                    errors.append(
                        ValidationError(
                            field="performance",
                            message=issue.title,
                            suggestion=issue.recommendation,
                        )
                    )
                elif issue.severity == IssueSeverity.MEDIUM:
                    warnings.append(
                        ValidationWarning(
                            field="performance",
                            message=issue.title,
                            suggestion=issue.recommendation,
                        )
                    )

        # Generate suggestions
        suggestions = self._generate_suggestions(
            workflow, errors, warnings, credential_requirements
        )

        # Determine overall status
        if errors:
            status = ValidationStatus.FAILED
        elif warnings:
            status = ValidationStatus.WARNINGS
        else:
            status = ValidationStatus.PASSED

        return ValidationReport(
            status=status,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            is_valid_schema=is_valid_schema,
            security_issues=security_issues,
            missing_nodes=missing_nodes,
            credential_requirements=credential_requirements,
            estimated_cost=estimated_cost,
            complexity_score=complexity_score,
            compatibility_score=compatibility_score,
            validated_at=datetime.utcnow(),
            validation_level=level,
        )

    def _validate_schema(
        self, workflow: Dict[str, Any], errors: List[ValidationError]
    ) -> bool:
        """Validate basic workflow schema"""

        required_fields = ["name", "nodes", "connections"]
        is_valid = True

        for field in required_fields:
            if field not in workflow:
                errors.append(
                    ValidationError(
                        field=field, message=f"Required field '{field}' is missing"
                    )
                )
                is_valid = False

        # Validate nodes structure
        if "nodes" in workflow:
            if not isinstance(workflow["nodes"], list):
                errors.append(
                    ValidationError(field="nodes", message="Nodes must be a list")
                )
                is_valid = False
            else:
                for i, node in enumerate(workflow["nodes"]):
                    if not isinstance(node, dict):
                        errors.append(
                            ValidationError(
                                field=f"nodes[{i}]", message="Node must be a dictionary"
                            )
                        )
                        is_valid = False
                    elif "type" not in node:
                        errors.append(
                            ValidationError(
                                field=f"nodes[{i}]",
                                message="Node missing required 'type' field",
                            )
                        )
                        is_valid = False

        # Validate connections structure
        if "connections" in workflow:
            if not isinstance(workflow["connections"], dict):
                errors.append(
                    ValidationError(
                        field="connections", message="Connections must be a dictionary"
                    )
                )
                is_valid = False

        return is_valid

    def _validate_security(
        self,
        workflow: Dict[str, Any],
        errors: List[ValidationError],
        warnings: List[ValidationWarning],
    ) -> List[Dict[str, Any]]:
        """Validate security aspects of the workflow"""

        security_issues = []
        workflow_str = json.dumps(workflow)

        # Check for hardcoded secrets
        for secret_type, pattern in self.secret_patterns.items():
            matches = pattern.findall(workflow_str)
            if matches:
                for match in matches:
                    security_issues.append(
                        {
                            "type": secret_type,
                            "found": len(matches),
                            "severity": "critical",
                        }
                    )
                    errors.append(
                        ValidationError(
                            field="security",
                            message=f"Found hardcoded {secret_type} in workflow",
                            severity="critical",
                            suggestion=f"Remove hardcoded {secret_type} and use n8n credentials instead",
                        )
                    )

        # Check for unsafe URLs
        unsafe_urls = re.findall(r'http://[^\s"\']+', workflow_str)
        if unsafe_urls:
            for url in unsafe_urls:
                if "localhost" not in url and "127.0.0.1" not in url:
                    warnings.append(
                        ValidationWarning(
                            field="security",
                            message=f"Unencrypted HTTP URL found: {url}",
                            suggestion="Use HTTPS for external connections",
                        )
                    )

        # Check webhook security
        for node in workflow.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.webhook":
                params = node.get("parameters", {})
                if not params.get("authentication"):
                    warnings.append(
                        ValidationWarning(
                            field=f"node.{node.get('name', node.get('id'))}",
                            message="Webhook without authentication",
                            suggestion="Add authentication to webhook",
                        )
                    )

        return security_issues

    def _validate_nodes(
        self, workflow: Dict[str, Any], errors: List[ValidationError]
    ) -> List[str]:
        """Check if all nodes are available"""

        missing_nodes = []

        for node in workflow.get("nodes", []):
            node_type = node.get("type")
            if node_type and node_type not in self.available_nodes:
                missing_nodes.append(node_type)
                errors.append(
                    ValidationError(
                        field=f"node.{node.get('name', node.get('id'))}",
                        message=f"Node type '{node_type}' is not available",
                        suggestion="Install the required node package or use an alternative",
                    )
                )

        return list(set(missing_nodes))

    def _extract_credentials(
        self, workflow: Dict[str, Any]
    ) -> List[CredentialRequirement]:
        """Extract credential requirements from workflow"""

        requirements = []

        for node in workflow.get("nodes", []):
            node_type = node.get("type", "")
            node_id = node.get("id", node.get("name", "unknown"))

            # Check for credential requirements based on node type
            credential_type = None

            if "slack" in node_type.lower():
                credential_type = "slackApi"
            elif "gmail" in node_type.lower():
                credential_type = "gmailOAuth2"
            elif "postgres" in node_type.lower():
                credential_type = "postgresDb"
            elif "supabase" in node_type.lower():
                credential_type = "supabaseApi"
            elif "openai" in node_type.lower() or "openAi" in node_type:
                credential_type = "openAiApi"
            elif "anthropic" in node_type.lower():
                credential_type = "anthropicApi"

            if credential_type:
                # Check if we have a mapping for this credential
                is_available = credential_type in self.available_credentials
                suggested_mapping = self.available_credentials.get(credential_type)

                requirements.append(
                    CredentialRequirement(
                        type=credential_type,
                        name=f"{credential_type} for {node.get('name', node_id)}",
                        node_id=node_id,
                        is_available=is_available,
                        suggested_mapping=suggested_mapping,
                    )
                )

        return requirements

    def _calculate_compatibility_score(
        self,
        missing_nodes: List[str],
        credential_requirements: List[CredentialRequirement],
    ) -> float:
        """Calculate overall compatibility score"""

        score = 100.0

        # Deduct for missing nodes (10 points each)
        score -= len(missing_nodes) * 10

        # Deduct for missing credentials (5 points each)
        missing_creds = [cr for cr in credential_requirements if not cr.is_available]
        score -= len(missing_creds) * 5

        return max(0.0, score)

    def _generate_suggestions(
        self,
        workflow: Dict[str, Any],
        errors: List[ValidationError],
        warnings: List[ValidationWarning],
        credential_requirements: List[CredentialRequirement],
    ) -> List[str]:
        """Generate helpful suggestions for fixing issues"""

        suggestions = []

        # Workflow naming
        if not workflow.get("name") or workflow.get("name") == "My workflow":
            suggestions.append("Give the workflow a descriptive name")

        # Add description
        if not workflow.get("description"):
            suggestions.append("Add a description explaining what this workflow does")

        # Credential mapping
        unmapped_creds = [cr for cr in credential_requirements if not cr.is_available]
        if unmapped_creds:
            suggestions.append(
                f"Map {len(unmapped_creds)} credential(s) to your environment"
            )

        # Error handling
        if not workflow.get("settings", {}).get("errorWorkflow"):
            suggestions.append(
                "Consider adding an error workflow for better reliability"
            )

        # Performance
        node_count = len(workflow.get("nodes", []))
        if node_count > 20:
            suggestions.append(
                "Consider breaking this workflow into smaller sub-workflows"
            )

        return suggestions


def validate_workflow_json(
    workflow_json: str, level: ValidationLevel = ValidationLevel.FULL
) -> ValidationReport:
    """Convenience function to validate workflow from JSON string"""

    try:
        workflow = json.loads(workflow_json)
    except json.JSONDecodeError as e:
        # Return error report for invalid JSON
        return ValidationReport(
            status=ValidationStatus.FAILED,
            errors=[
                ValidationError(
                    field="json", message=f"Invalid JSON: {str(e)}", severity="critical"
                )
            ],
            warnings=[],
            suggestions=["Fix JSON syntax errors before importing"],
            is_valid_schema=False,
            security_issues=[],
            missing_nodes=[],
            credential_requirements=[],
            estimated_cost=0.0,
            complexity_score=0,
            compatibility_score=0.0,
            validated_at=datetime.utcnow(),
            validation_level=level,
        )

    validator = WorkflowValidator()
    return validator.validate(workflow, level)


def validate_workflow_file(
    file_path: str, level: ValidationLevel = ValidationLevel.FULL
) -> ValidationReport:
    """Validate workflow from file"""

    try:
        with open(file_path, "r") as f:
            workflow_json = f.read()
        return validate_workflow_json(workflow_json, level)
    except Exception as e:
        return ValidationReport(
            status=ValidationStatus.FAILED,
            errors=[
                ValidationError(
                    field="file",
                    message=f"Failed to read file: {str(e)}",
                    severity="critical",
                )
            ],
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
            validation_level=level,
        )
