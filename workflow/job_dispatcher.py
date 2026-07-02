"""Job dispatcher for NTPE Stage-09.1."""
from __future__ import annotations
from typing import Any, Dict
import time

from .job_models import Job, JobContext, JobResult, JobStatus
from .scheduling_policy import SchedulingPolicy

class JobDispatcher:
    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, policy: SchedulingPolicy | None = None) -> None:
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.policy = policy or SchedulingPolicy()

    def _publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.jobs", source="job_dispatcher")

    def dispatch(self, job: Job) -> JobResult:
        if job.cancelled:
            job.mark(JobStatus.CANCELLED)
            self._publish("job.cancelled", {"job_id": job.job_id, "name": job.name})
            return JobResult(False, job.job_id, job.status, error="cancelled", attempts=job.attempts)

        while True:
            job.attempts += 1
            job.mark(JobStatus.RUNNING)
            self._publish("job.started", {"job_id": job.job_id, "name": job.name, "attempts": job.attempts})
            started = time.time()
            try:
                if job.timeout_seconds is not None and job.timeout_seconds <= 0:
                    raise TimeoutError("job timeout before execution")
                context = JobContext(job_id=job.job_id, workflow_name=job.workflow_name, metadata=dict(job.metadata))
                if job.action is not None:
                    output = job.action(context=context, payload=job.payload, services=self.service_container)
                elif job.workflow_name and self.workflow_core is not None:
                    output = self.workflow_core.execute(job.workflow_name, **job.payload)
                else:
                    output = {"job": job.name, "payload": dict(job.payload)}
                if job.timeout_seconds is not None and (time.time() - started) > job.timeout_seconds:
                    raise TimeoutError("job execution timeout")
                job.result = output
                job.error = None
                job.mark(JobStatus.COMPLETED)
                self._publish("job.completed", {"job_id": job.job_id, "name": job.name, "attempts": job.attempts})
                return JobResult(True, job.job_id, job.status, output=output, attempts=job.attempts)
            except TimeoutError as exc:
                job.error = str(exc)
                job.mark(JobStatus.TIMEOUT)
                self._publish("job.timeout", {"job_id": job.job_id, "error": str(exc), "attempts": job.attempts})
                return JobResult(False, job.job_id, job.status, error=str(exc), attempts=job.attempts)
            except Exception as exc:  # noqa: BLE001 - scheduler isolates job failures
                job.error = str(exc)
                if self.policy.should_retry(job):
                    job.mark(JobStatus.RETRYING)
                    self._publish("job.retrying", {"job_id": job.job_id, "error": str(exc), "attempts": job.attempts})
                    continue
                job.mark(JobStatus.FAILED)
                self._publish("job.failed", {"job_id": job.job_id, "error": str(exc), "attempts": job.attempts})
                return JobResult(False, job.job_id, job.status, error=str(exc), attempts=job.attempts)
