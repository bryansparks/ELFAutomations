"""
N8N Integration Models
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkflowStatus(Enum):
    """Workflow execution status"""

    PENDING = "pending"
    RUNNING = "running"
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

    DATA_PIPELINE = "data-pipeline"
    INTEGRATION = "integration"
    AUTOMATION = "automation"
    NOTIFICATION = "notification"
    APPROVAL = "approval"


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
