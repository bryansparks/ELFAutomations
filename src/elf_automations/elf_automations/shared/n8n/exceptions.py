"""
N8N Integration Exceptions
"""


class N8NError(Exception):
    """Base exception for N8N integration errors"""

    pass


class WorkflowExecutionError(N8NError):
    """Raised when workflow execution fails"""

    def __init__(self, workflow_name: str, error_message: str):
        self.workflow_name = workflow_name
        self.error_message = error_message
        super().__init__(
            f"Workflow '{workflow_name}' execution failed: {error_message}"
        )


class WorkflowNotFoundError(N8NError):
    """Raised when requested workflow doesn't exist"""

    def __init__(self, workflow_name: str):
        self.workflow_name = workflow_name
        super().__init__(f"Workflow '{workflow_name}' not found in registry")


class WorkflowValidationError(N8NError):
    """Raised when workflow validation fails"""

    def __init__(self, message: str, errors: list = None):
        self.errors = errors or []
        super().__init__(message)
