"""
N8N Integration Module for ELF Automations

Provides SDK and utilities for teams to interact with n8n workflows.
"""

from .client import N8NClient
from .exceptions import N8NError, WorkflowExecutionError, WorkflowNotFoundError
from .models import (
    WorkflowSpec, 
    WorkflowExecution, 
    WorkflowStatus,
    WorkflowCategory,
    WorkflowTriggerType,
    WorkflowInfo
)

__all__ = [
    'N8NClient',
    'N8NError',
    'WorkflowExecutionError',
    'WorkflowNotFoundError',
    'WorkflowSpec',
    'WorkflowExecution',
    'WorkflowStatus',
    'WorkflowCategory',
    'WorkflowTriggerType',
    'WorkflowInfo'
]