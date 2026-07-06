# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

class WorkflowError(Exception):
    """Base error for Translation Workflow Engine."""


class WorkflowInputError(WorkflowError, ValueError):
    """Raised when workflow input is invalid."""


class WorkflowStepError(WorkflowError):
    """Raised when a workflow step fails."""
