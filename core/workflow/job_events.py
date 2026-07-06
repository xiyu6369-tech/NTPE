# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager
# =====================================================

from __future__ import annotations

from .workflow_events import WorkflowEventBus

JOB_ENQUEUED = "JobEnqueued"
JOB_STARTED = "JobStarted"
JOB_COMPLETED = "JobCompleted"
JOB_FAILED = "JobFailed"
JOB_RETRY = "JobRetry"
JOB_PAUSED = "JobPaused"
JOB_RESUMED = "JobResumed"


class JobEventBus(WorkflowEventBus):
    """Stage-17.2 scheduler event bus, compatible with WorkflowEventBus."""
