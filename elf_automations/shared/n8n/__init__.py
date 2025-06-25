"""
N8N Integration Module for ELF Automations

Provides SDK and utilities for teams to interact with n8n workflows.
"""

from .client import N8NClient
from .config import (
    NotificationSettings,
    ServicePreferences,
    TeamConfiguration,
    WorkflowConfig,
    WorkflowDefaults,
)
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
from .patterns import (
    InputSource,
    NodeMapper,
    OutputChannel,
    StorageType,
    WorkflowPattern,
    WorkflowPatterns,
    detect_pattern,
    generate_pattern_nodes,
)
from .workflow_exporter import WorkflowExporter
from .workflow_importer import WorkflowImporter
from .workflow_validator import ValidationReport, WorkflowValidator

__all__ = [
    # Client and exceptions
    "N8NClient",
    "N8NError",
    "WorkflowExecutionError",
    "WorkflowNotFoundError",
    "WorkflowValidationError",
    # Models
    "WorkflowSpec",
    "WorkflowExecution",
    "WorkflowStatus",
    "WorkflowCategory",
    "WorkflowTriggerType",
    "WorkflowInfo",
    "WorkflowSource",
    "ValidationStatus",
    # Import/Export/Validation
    "WorkflowImporter",
    "WorkflowExporter",
    "WorkflowValidator",
    "ValidationReport",
    # Patterns
    "WorkflowPattern",
    "WorkflowPatterns",
    "InputSource",
    "StorageType",
    "OutputChannel",
    "detect_pattern",
    "generate_pattern_nodes",
    "NodeMapper",
    # Configuration
    "WorkflowConfig",
    "ServicePreferences",
    "NotificationSettings",
    "WorkflowDefaults",
    "TeamConfiguration",
]
