"""Workflow Job Scheduler for NTPE 1.0 Beta Stage-09.1."""
from __future__ import annotations
from typing import Any, Callable

from .job_manager import JobManager
from .job_models import JOB_SCHEDULER_STAGE, JOB_SCHEDULER_VERSION, JobPriority
from .scheduling_policy import SchedulingPolicy

class JobScheduler:
    version = JOB_SCHEDULER_VERSION
    stage = JOB_SCHEDULER_STAGE

    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, policy: SchedulingPolicy | None = None, metadata: dict | None = None) -> None:
        self.manager = JobManager(event_bus=event_bus, service_container=service_container, workflow_core=workflow_core, policy=policy)
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.metadata = dict(metadata or {})

    def create_job(self, name: str, action: Callable[..., Any] | None = None, **kwargs: Any):
        return self.manager.create_job(name, action, **kwargs)

    def schedule(self, job):
        return self.manager.schedule(job)

    def schedule_job(self, name: str, action: Callable[..., Any] | None = None, **kwargs: Any):
        return self.manager.schedule_new(name, action, **kwargs)

    def run_next(self):
        return self.manager.run_next()

    def run_all(self) -> list:
        return self.manager.run_all()

    def cancel(self, job_id: str):
        return self.manager.cancel(job_id)

    def resume(self, job_id: str):
        return self.manager.resume(job_id)

    def status(self, job_id: str) -> str:
        return self.manager.status(job_id)

    def manifest(self) -> dict:
        base = self.manager.manifest()
        base.update({"version": self.version, "stage": self.stage, "metadata": dict(self.metadata)})
        return base

def create_job_scheduler(**kwargs: Any) -> JobScheduler:
    return JobScheduler(**kwargs)
