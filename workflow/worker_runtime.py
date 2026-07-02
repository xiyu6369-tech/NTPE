"""Public Worker Runtime API for NTPE 1.0 Beta Stage-09.4."""
from __future__ import annotations
from typing import Any, Callable

from .task_models import Task, TaskPriority
from .worker_manager import WorkerManager
from .worker_models import WORKER_RUNTIME_STAGE, WORKER_RUNTIME_VERSION, WorkerRuntimeStatus

class WorkerRuntime:
    version = WORKER_RUNTIME_VERSION
    stage = WORKER_RUNTIME_STAGE

    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, job_scheduler: Any = None, pipeline_orchestrator: Any = None, task_queue: Any = None, metadata: dict | None = None, worker_count: int = 1) -> None:
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.job_scheduler = job_scheduler
        self.pipeline_orchestrator = pipeline_orchestrator
        self.task_queue = task_queue
        task_dispatcher = getattr(getattr(task_queue, "manager", None), "dispatcher", None)
        self.manager = WorkerManager(event_bus=event_bus, service_container=service_container, task_queue=task_queue, task_dispatcher=task_dispatcher)
        self.metadata = dict(metadata or {})
        self.status = WorkerRuntimeStatus.CREATED
        for index in range(worker_count):
            self.manager.create_worker(f"worker-{index + 1}", runtime_stage="09.4")

    def _publish(self, event_type: str, payload: dict) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.workers", source="worker_runtime")

    def start(self) -> "WorkerRuntime":
        self.status = WorkerRuntimeStatus.RUNNING
        self._publish("worker.runtime.started", {"stage": self.stage})
        return self

    def stop(self) -> "WorkerRuntime":
        self.status = WorkerRuntimeStatus.STOPPED
        for worker in self.manager.pool.all():
            self.manager.stop_worker(worker.worker_id)
        self._publish("worker.runtime.stopped", {"stage": self.stage})
        return self

    def create_worker(self, name: str, **metadata: Any):
        return self.manager.create_worker(name, **metadata)

    def create_task(self, name: str, action: Callable[..., Any] | None = None, *, priority: TaskPriority | int = TaskPriority.NORMAL, payload: dict | None = None, **kwargs: Any) -> Task:
        return Task(name=name, action=action, priority=priority, payload=dict(payload or {}), **kwargs)

    def execute_task(self, task: Task, *, timeout: float | None = None):
        if self.status == WorkerRuntimeStatus.CREATED:
            self.start()
        return self.manager.execute(task, timeout=timeout)

    def run_next(self, *, timeout: float | None = None):
        if self.status == WorkerRuntimeStatus.CREATED:
            self.start()
        return self.manager.run_next(timeout=timeout)

    def run_all(self, *, timeout: float | None = None):
        if self.status == WorkerRuntimeStatus.CREATED:
            self.start()
        return self.manager.run_all(timeout=timeout)

    def manifest(self) -> dict:
        return {
            "version": self.version,
            "stage": self.stage,
            "status": self.status.value,
            "foundation_status": "frozen",
            "integration_status": "frozen",
            "workflow_core_compatible": True,
            "job_scheduler_compatible": True,
            "pipeline_orchestrator_compatible": True,
            "task_queue_compatible": True,
            "additive_only": True,
            "bridges": {
                "event_bus_attached": self.event_bus is not None,
                "service_container_attached": self.service_container is not None,
                "workflow_core_attached": self.workflow_core is not None,
                "job_scheduler_attached": self.job_scheduler is not None,
                "pipeline_orchestrator_attached": self.pipeline_orchestrator is not None,
                "task_queue_attached": self.task_queue is not None,
            },
            "manager": self.manager.manifest(),
            "metadata": dict(self.metadata),
        }

def create_worker_runtime(**kwargs: Any) -> WorkerRuntime:
    return WorkerRuntime(**kwargs)
