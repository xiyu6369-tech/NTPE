"""Worker manager for NTPE Stage-09.4."""
from __future__ import annotations
from typing import Any

from .task_models import Task
from .task_result import TaskResult
from .worker_dispatcher import WorkerDispatcher
from .worker_models import Worker, WorkerStatus
from .worker_pool import WorkerPool
from .worker_registry import WorkerRegistry

class WorkerManager:
    def __init__(self, *, event_bus: Any = None, service_container: Any = None, task_queue: Any = None, task_dispatcher: Any = None) -> None:
        self.event_bus = event_bus
        self.service_container = service_container
        self.task_queue = task_queue
        self.registry = WorkerRegistry()
        self.pool = WorkerPool()
        self.dispatcher = WorkerDispatcher(event_bus=event_bus, service_container=service_container, task_dispatcher=task_dispatcher)

    def _publish(self, event_type: str, payload: dict) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.workers", source="worker_manager")

    def create_worker(self, name: str, **metadata: Any) -> Worker:
        worker = Worker(name=name, metadata=dict(metadata))
        self.registry.register(worker)
        self.pool.add(worker)
        self._publish("worker.created", {"worker_id": worker.worker_id, "name": worker.name})
        return worker

    def stop_worker(self, worker_id: str) -> Worker:
        worker = self.registry.get(worker_id)
        worker.mark(WorkerStatus.STOPPED)
        self._publish("worker.stopped", {"worker_id": worker.worker_id, "name": worker.name})
        return worker

    def execute(self, task: Task, *, worker_id: str | None = None, timeout: float | None = None) -> TaskResult:
        worker = self.registry.get(worker_id) if worker_id else self.pool.acquire()
        if worker is None:
            worker = self.create_worker("default-worker")
        return self.dispatcher.dispatch(worker, task, timeout=timeout)

    def run_next(self, *, timeout: float | None = None) -> TaskResult | None:
        if self.task_queue is None:
            return None
        queue_obj = getattr(self.task_queue, "manager", self.task_queue)
        task = queue_obj.queue.pop() if hasattr(queue_obj, "queue") else None
        if task is None:
            return None
        return self.execute(task, timeout=timeout)

    def run_all(self, *, timeout: float | None = None) -> list[TaskResult]:
        results: list[TaskResult] = []
        while True:
            result = self.run_next(timeout=timeout)
            if result is None:
                break
            results.append(result)
        return results

    def manifest(self) -> dict:
        return {"registry": self.registry.manifest(), "pool": self.pool.manifest()}
