# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager
# =====================================================

from __future__ import annotations

from .job_context import JobContext
from .job_events import JOB_COMPLETED, JOB_FAILED, JOB_RETRY, JOB_STARTED, JobEventBus
from .job_result import JobResult
from .job_state import JOB_COMPLETED as STATUS_COMPLETED, JOB_FAILED as STATUS_FAILED, JOB_RUNNING
from .workflow_context import WorkflowContext
from .workflow_engine import TranslationWorkflowEngine


class JobWorker:
    """Synchronous worker that binds JobContext to TranslationWorkflowEngine."""

    def __init__(self, workflow_engine: TranslationWorkflowEngine | None = None, event_bus: JobEventBus | None = None) -> None:
        self.workflow_engine = workflow_engine or TranslationWorkflowEngine()
        self.event_bus = event_bus or JobEventBus()

    def run(self, job: JobContext) -> JobResult:
        job.state.attempts += 1
        job.state.mark(JOB_RUNNING, progress=0.1)
        self.event_bus.emit(JOB_STARTED, job_id=job.job_id, attempt=job.state.attempts)
        try:
            workflow_context = WorkflowContext(source_text=job.source_text, metadata=dict(job.metadata))
            workflow_result = self.workflow_engine.run(workflow_context)
            if not workflow_result.success:
                raise RuntimeError("workflow execution failed")
            job.state.mark(STATUS_COMPLETED, progress=1.0)
            self.event_bus.emit(JOB_COMPLETED, job_id=job.job_id)
            return JobResult(job.job_id, STATUS_COMPLETED, workflow_result, job.state.attempts, artifacts=workflow_result.artifacts)
        except Exception as exc:
            if job.state.can_retry:
                self.event_bus.emit(JOB_RETRY, job_id=job.job_id, attempt=job.state.attempts, error=str(exc))
            job.state.mark(STATUS_FAILED, progress=job.state.progress, error=str(exc))
            self.event_bus.emit(JOB_FAILED, job_id=job.job_id, error=str(exc))
            return JobResult(job.job_id, STATUS_FAILED, None, job.state.attempts, error=str(exc))
