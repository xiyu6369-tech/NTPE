# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager
# =====================================================

from __future__ import annotations

from .workflow_exceptions import WorkflowError


class JobSchedulerError(WorkflowError):
    """Base exception for Stage-17.2 job scheduling."""


class JobQueueError(JobSchedulerError):
    """Raised when the job queue cannot accept or return a job."""


class JobExecutionError(JobSchedulerError):
    """Raised when a job fails during workflow execution."""
