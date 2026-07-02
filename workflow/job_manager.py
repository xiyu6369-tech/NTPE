"""Job manager for NTPE Stage-09.1."""
from __future__ import annotations
from typing import Any, Callable

from .job_dispatcher import JobDispatcher
from .job_models import Job, JobPriority, JobStatus
from .job_queue import JobQueue
from .job_registry import JobRegistry
from .scheduling_policy import SchedulingPolicy

class JobManager:
    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, policy: SchedulingPolicy | None = None) -> None:
        self.registry = JobRegistry()
        self.queue = JobQueue()
        self.policy = policy or SchedulingPolicy()
        self.dispatcher = JobDispatcher(event_bus=event_bus, service_container=service_container, workflow_core=workflow_core, policy=self.policy)
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core

    def _publish(self, event_type: str, payload: dict) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.jobs", source="job_manager")

    def create_job(self, name: str, action: Callable[..., Any] | None = None, *, priority: JobPriority | int = JobPriority.NORMAL, payload: dict | None = None, workflow_name: str | None = None, max_retries: int = 0, timeout_seconds: float | None = None, **metadata: Any) -> Job:
        job = Job(name=name, action=action, priority=priority, payload=dict(payload or {}), workflow_name=workflow_name, max_retries=max_retries, timeout_seconds=timeout_seconds, metadata=dict(metadata))
        self.policy.normalize(job)
        self.registry.register(job)
        self._publish("job.created", {"job_id": job.job_id, "name": job.name})
        return job

    def schedule(self, job: Job) -> Job:
        self.registry.register(job)
        self.queue.push(job)
        self._publish("job.queued", {"job_id": job.job_id, "name": job.name, "priority": int(job.priority)})
        return job

    def schedule_new(self, name: str, action: Callable[..., Any] | None = None, **kwargs: Any) -> Job:
        return self.schedule(self.create_job(name, action, **kwargs))

    def run_next(self):
        job = self.queue.pop()
        return self.dispatcher.dispatch(job)

    def run_all(self) -> list:
        results = []
        while not self.queue.empty():
            results.append(self.run_next())
        return results

    def cancel(self, job_id: str) -> Job:
        job = self.registry.get(job_id)
        job.cancelled = True
        if job.status in {JobStatus.CREATED, JobStatus.QUEUED}:
            job.mark(JobStatus.CANCELLED)
            self._publish("job.cancelled", {"job_id": job.job_id, "name": job.name})
        return job

    def resume(self, job_id: str) -> Job:
        job = self.registry.get(job_id)
        if job.status in {JobStatus.FAILED, JobStatus.TIMEOUT, JobStatus.CANCELLED}:
            job.cancelled = False
            job.error = None
            self.schedule(job)
        return job

    def status(self, job_id: str) -> str:
        return self.registry.status(job_id)

    def manifest(self) -> dict:
        return {
            "stage": "NTPE 1.0 Beta Stage-09.1 Job Scheduler",
            "foundation_status": "frozen",
            "integration_status": "frozen",
            "workflow_core_compatible": True,
            "additive_only": True,
            "queue_size": len(self.queue),
            "registry": self.registry.manifest(),
            "bridges": {
                "event_bus_attached": self.event_bus is not None,
                "service_container_attached": self.service_container is not None,
                "workflow_core_attached": self.workflow_core is not None,
            },
        }
