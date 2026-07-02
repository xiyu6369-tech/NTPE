"""Public Task Queue API for NTPE 1.0 Beta Stage-09.3."""
from __future__ import annotations
from typing import Any, Callable
from .task_models import TASK_QUEUE_STAGE, TASK_QUEUE_VERSION, Task, TaskPriority
from .task_queue_manager import TaskQueueManager

class WorkflowTaskQueue:
    version = TASK_QUEUE_VERSION
    stage = TASK_QUEUE_STAGE

    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, job_scheduler: Any = None, pipeline_orchestrator: Any = None, metadata: dict | None = None) -> None:
        self.manager = TaskQueueManager(event_bus=event_bus, service_container=service_container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline_orchestrator)
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.job_scheduler = job_scheduler
        self.pipeline_orchestrator = pipeline_orchestrator
        self.metadata = dict(metadata or {})

    def create_task(self, name: str, action: Callable[..., Any] | None = None, *, priority: TaskPriority | int = TaskPriority.NORMAL, payload: dict | None = None, **kwargs: Any) -> Task:
        return self.manager.create_task(name, action, priority=priority, payload=payload, **kwargs)

    def enqueue(self, task: Task) -> Task:
        return self.manager.enqueue(task)

    def enqueue_task(self, name: str, action: Callable[..., Any] | None = None, **kwargs: Any) -> Task:
        return self.manager.enqueue_task(name, action, **kwargs)

    def cancel(self, task_id: str) -> Task:
        return self.manager.cancel(task_id)

    def run_next(self):
        return self.manager.run_next()

    def run_all(self):
        return self.manager.run_all()

    def status(self, task_id: str) -> str:
        return self.manager.status(task_id)

    def metrics(self) -> dict:
        return self.manager.metrics().to_dict()

    def manifest(self) -> dict:
        base = self.manager.manifest()
        base.update({
            "version": self.version,
            "stage": self.stage,
            "foundation_status": "frozen",
            "integration_status": "frozen",
            "workflow_core_compatible": True,
            "job_scheduler_compatible": True,
            "pipeline_orchestrator_compatible": True,
            "additive_only": True,
            "bridges": {
                "event_bus_attached": self.event_bus is not None,
                "service_container_attached": self.service_container is not None,
                "workflow_core_attached": self.workflow_core is not None,
                "job_scheduler_attached": self.job_scheduler is not None,
                "pipeline_orchestrator_attached": self.pipeline_orchestrator is not None,
            },
            "metadata": dict(self.metadata),
        })
        return base

def create_task_queue(**kwargs: Any) -> WorkflowTaskQueue:
    return WorkflowTaskQueue(**kwargs)
