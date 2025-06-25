"""
N8N Integration Models
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkflowStatus(Enum):
    """Workflow lifecycle status"""

    IMPORTED = "imported"  # Just imported, not yet validated
    VALIDATING = "validating"  # Currently being validated
    VALIDATED = "validated"  # Passed validation, ready for testing
    TESTING = "testing"  # Under test/validation
    APPROVED = "approved"  # Approved and ready for deployment
    DEPLOYED = "deployed"  # Actively deployed in n8n
    RUNNING = "running"  # Active and executable
    PAUSED = "paused"  # Temporarily disabled
    DEPRECATED = "deprecated"  # Phased out, kept for history
    ARCHIVED = "archived"  # Archived, not active

    # Legacy execution statuses (for backward compatibility)
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class WorkflowTriggerType(Enum):
    """Types of workflow triggers"""

    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    EVENT = "event"


class WorkflowCategory(Enum):
    """Categories of workflows"""

    CUSTOMER_ONBOARDING = "customer_onboarding"
    ORDER_PROCESSING = "order_processing"
    DATA_PIPELINE = "data_pipeline"
    DATA_SYNC = "data_sync"
    REPORTING = "reporting"
    MARKETING_AUTOMATION = "marketing_automation"
    TEAM_COORDINATION = "team_coordination"
    MAINTENANCE = "maintenance"
    INTEGRATION = "integration"
    NOTIFICATION = "notification"
    APPROVAL = "approval"
    AUTOMATION = "automation"
    OTHER = "other"

    # Legacy values for compatibility
    DATA_PIPELINE_LEGACY = "data-pipeline"

    @classmethod
    def from_string(cls, value: str) -> "WorkflowCategory":
        """Convert string to enum, handling legacy formats"""
        # Handle legacy hyphenated values
        normalized = value.replace("-", "_")
        try:
            return cls(normalized)
        except ValueError:
            # Try exact match first
            for member in cls:
                if member.value == value:
                    return member
            # Default to OTHER
            return cls.OTHER


class WorkflowSource(Enum):
    """Source of workflow"""

    N8N_EXPORT = "n8n_export"  # Exported from N8N UI
    TEMPLATE = "template"  # Created from template
    API_IMPORT = "api_import"  # Imported via API
    TEAM_CREATED = "team_created"  # Created by a team
    MIGRATION = "migration"  # Migrated from another system


class ValidationStatus(Enum):
    """Validation status"""

    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class WorkflowSpec:
    """Specification for creating a new workflow"""

    name: str
    description: str
    category: WorkflowCategory
    owner_team: str
    trigger_type: WorkflowTriggerType
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    nodes: Optional[List[Dict[str, Any]]] = None
    credentials: Optional[Dict[str, str]] = None
    settings: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowExecution:
    """Represents a workflow execution"""

    id: str
    workflow_id: str
    workflow_name: str
    triggered_by: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: WorkflowStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]

    @property
    def duration(self) -> Optional[float]:
        """Calculate execution duration in seconds"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_complete(self) -> bool:
        """Check if execution is complete"""
        return self.status in [WorkflowStatus.SUCCESS, WorkflowStatus.FAILED]


@dataclass
class WorkflowInfo:
    """Information about a registered workflow"""

    id: str
    name: str
    description: str
    category: WorkflowCategory
    owner_team: str
    n8n_workflow_id: str
    trigger_type: WorkflowTriggerType
    webhook_url: Optional[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    execution_count: Optional[int] = 0
    success_rate: Optional[float] = None
