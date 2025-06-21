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
from .exceptions import N8NError, WorkflowExecutionError, WorkflowNotFoundError
from .models import (
    WorkflowCategory,
    WorkflowExecution,
    WorkflowInfo,
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

__all__ = [
    # Client and exceptions
    "N8NClient",
    "N8NError",
    "WorkflowExecutionError",
    "WorkflowNotFoundError",
    # Models
    "WorkflowSpec",
    "WorkflowExecution",
    "WorkflowStatus",
    "WorkflowCategory",
    "WorkflowTriggerType",
    "WorkflowInfo",
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
