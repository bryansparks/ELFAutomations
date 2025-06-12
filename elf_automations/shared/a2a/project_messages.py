"""
Project-related A2A message types for autonomous coordination.

These messages enable teams to coordinate on projects without human intervention.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .messages import A2AMessage


class ProjectMessageType(Enum):
    """Types of project-related messages."""
    PROJECT_ASSIGNMENT = "project_assignment"
    TASK_ASSIGNMENT = "task_assignment"
    PROGRESS_UPDATE = "progress_update"
    DEPENDENCY_COMPLETE = "dependency_complete"
    BLOCKER_REPORTED = "blocker_reported"
    HELP_REQUESTED = "help_requested"
    RESOURCE_REQUEST = "resource_request"
    DEADLINE_WARNING = "deadline_warning"
    TASK_HANDOFF = "task_handoff"


@dataclass
class ProjectAssignmentMessage(A2AMessage):
    """Message to assign a project to a team."""
    project_id: str
    project_name: str
    description: str
    priority: str
    deadline: Optional[str] = None
    assigned_tasks: List[str] = None
    
    def __post_init__(self):
        self.type = ProjectMessageType.PROJECT_ASSIGNMENT.value
        if self.assigned_tasks is None:
            self.assigned_tasks = []


@dataclass
class TaskAssignmentMessage(A2AMessage):
    """Message to assign a specific task to a team."""
    task_id: str
    task_title: str
    project_id: str
    project_name: str
    description: str
    required_skills: List[str]
    estimated_hours: Optional[float] = None
    due_date: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        self.type = ProjectMessageType.TASK_ASSIGNMENT.value
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class ProgressUpdateMessage(A2AMessage):
    """Message to update progress on a task or project."""
    task_id: str
    project_id: str
    status: str  # pending, ready, in_progress, blocked, review, completed
    progress_percentage: float
    hours_worked: float
    estimated_completion: Optional[str] = None
    blockers: List[Dict[str, str]] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        self.type = ProjectMessageType.PROGRESS_UPDATE.value
        if self.blockers is None:
            self.blockers = []


@dataclass 
class DependencyCompleteMessage(A2AMessage):
    """Message to notify that a dependency is complete."""
    completed_task_id: str
    completed_task_title: str
    dependent_task_ids: List[str]
    project_id: str
    output_description: Optional[str] = None
    output_location: Optional[str] = None
    
    def __post_init__(self):
        self.type = ProjectMessageType.DEPENDENCY_COMPLETE.value


@dataclass
class BlockerReportedMessage(A2AMessage):
    """Message to report a blocker that needs resolution."""
    task_id: str
    task_title: str
    project_id: str
    blocker_description: str
    blocker_type: str  # technical, resource, dependency, external
    severity: str  # low, medium, high, critical
    suggested_resolution: Optional[str] = None
    needs_help_from: Optional[str] = None  # Specific team that can help
    
    def __post_init__(self):
        self.type = ProjectMessageType.BLOCKER_REPORTED.value


@dataclass
class HelpRequestedMessage(A2AMessage):
    """Message to request help from another team."""
    task_id: str
    project_id: str
    requesting_team: str
    help_type: str  # expertise, resources, review, debugging
    description: str
    required_skills: List[str]
    estimated_hours: Optional[float] = None
    urgency: str = "normal"  # low, normal, high, critical
    
    def __post_init__(self):
        self.type = ProjectMessageType.HELP_REQUESTED.value


@dataclass
class ResourceRequestMessage(A2AMessage):
    """Message to request additional resources for a project."""
    project_id: str
    project_name: str
    requesting_team: str
    resource_type: str  # team_member, compute, storage, external_service
    quantity_needed: float
    justification: str
    impact_if_denied: str
    alternative_solution: Optional[str] = None
    
    def __post_init__(self):
        self.type = ProjectMessageType.RESOURCE_REQUEST.value


@dataclass
class DeadlineWarningMessage(A2AMessage):
    """Message to warn about an at-risk deadline."""
    project_id: str
    project_name: str
    task_id: Optional[str] = None
    original_deadline: str
    predicted_completion: str
    delay_days: int
    risk_factors: List[str] = None
    mitigation_options: List[str] = None
    
    def __post_init__(self):
        self.type = ProjectMessageType.DEADLINE_WARNING.value
        if self.risk_factors is None:
            self.risk_factors = []
        if self.mitigation_options is None:
            self.mitigation_options = []


@dataclass
class TaskHandoffMessage(A2AMessage):
    """Message to hand off a task between teams."""
    task_id: str
    task_title: str
    project_id: str
    from_team: str
    to_team: str
    handoff_reason: str  # completed_portion, expertise_needed, capacity
    work_completed: str
    remaining_work: str
    context: Dict[str, Any] = None
    artifacts: List[str] = None  # Files, documents, etc.
    
    def __post_init__(self):
        self.type = ProjectMessageType.TASK_HANDOFF.value
        if self.context is None:
            self.context = {}
        if self.artifacts is None:
            self.artifacts = []


class ProjectCoordinator:
    """Helper class for project-related A2A communications."""
    
    @staticmethod
    def create_project_assignment(
        project_id: str,
        project_name: str,
        description: str,
        priority: str,
        sender: str,
        recipient: str,
        deadline: Optional[str] = None,
        assigned_tasks: Optional[List[str]] = None
    ) -> ProjectAssignmentMessage:
        """Create a project assignment message."""
        return ProjectAssignmentMessage(
            sender=sender,
            recipient=recipient,
            project_id=project_id,
            project_name=project_name,
            description=description,
            priority=priority,
            deadline=deadline,
            assigned_tasks=assigned_tasks or []
        )
    
    @staticmethod
    def create_progress_update(
        task_id: str,
        project_id: str,
        status: str,
        progress: float,
        hours_worked: float,
        sender: str,
        recipient: str,
        **kwargs
    ) -> ProgressUpdateMessage:
        """Create a progress update message."""
        return ProgressUpdateMessage(
            sender=sender,
            recipient=recipient,
            task_id=task_id,
            project_id=project_id,
            status=status,
            progress_percentage=progress,
            hours_worked=hours_worked,
            **kwargs
        )
    
    @staticmethod
    def create_blocker_report(
        task_id: str,
        task_title: str,
        project_id: str,
        blocker_description: str,
        severity: str,
        sender: str,
        recipient: str,
        **kwargs
    ) -> BlockerReportedMessage:
        """Create a blocker report message."""
        return BlockerReportedMessage(
            sender=sender,
            recipient=recipient,
            task_id=task_id,
            task_title=task_title,
            project_id=project_id,
            blocker_description=blocker_description,
            blocker_type=kwargs.get('blocker_type', 'technical'),
            severity=severity,
            **kwargs
        )
    
    @staticmethod
    def create_dependency_notification(
        completed_task_id: str,
        completed_task_title: str,
        dependent_task_ids: List[str],
        project_id: str,
        sender: str,
        recipients: List[str],
        **kwargs
    ) -> List[DependencyCompleteMessage]:
        """Create dependency complete notifications for multiple teams."""
        messages = []
        for recipient in recipients:
            msg = DependencyCompleteMessage(
                sender=sender,
                recipient=recipient,
                completed_task_id=completed_task_id,
                completed_task_title=completed_task_title,
                dependent_task_ids=dependent_task_ids,
                project_id=project_id,
                **kwargs
            )
            messages.append(msg)
        return messages
    
    @staticmethod
    def create_help_request(
        task_id: str,
        project_id: str,
        help_type: str,
        description: str,
        required_skills: List[str],
        sender: str,
        recipient: str,
        urgency: str = "normal",
        **kwargs
    ) -> HelpRequestedMessage:
        """Create a help request message."""
        return HelpRequestedMessage(
            sender=sender,
            recipient=recipient,
            task_id=task_id,
            project_id=project_id,
            requesting_team=sender,
            help_type=help_type,
            description=description,
            required_skills=required_skills,
            urgency=urgency,
            **kwargs
        )
    
    @staticmethod
    def parse_project_message(message_data: Dict[str, Any]) -> A2AMessage:
        """Parse a project message from raw data."""
        msg_type = message_data.get('type')
        
        message_classes = {
            ProjectMessageType.PROJECT_ASSIGNMENT.value: ProjectAssignmentMessage,
            ProjectMessageType.TASK_ASSIGNMENT.value: TaskAssignmentMessage,
            ProjectMessageType.PROGRESS_UPDATE.value: ProgressUpdateMessage,
            ProjectMessageType.DEPENDENCY_COMPLETE.value: DependencyCompleteMessage,
            ProjectMessageType.BLOCKER_REPORTED.value: BlockerReportedMessage,
            ProjectMessageType.HELP_REQUESTED.value: HelpRequestedMessage,
            ProjectMessageType.RESOURCE_REQUEST.value: ResourceRequestMessage,
            ProjectMessageType.DEADLINE_WARNING.value: DeadlineWarningMessage,
            ProjectMessageType.TASK_HANDOFF.value: TaskHandoffMessage,
        }
        
        message_class = message_classes.get(msg_type)
        if not message_class:
            raise ValueError(f"Unknown project message type: {msg_type}")
        
        # Remove type field as it's set in __post_init__
        data = {k: v for k, v in message_data.items() if k != 'type'}
        
        return message_class(**data)