"""Task queue manager for NTPE Stage-09.3."""
from __future__ import annotations
from typing import Any, Callable
from .queue_metrics import QueueMetrics
from .task_dispatcher import TaskDispatcher
from .task_models import Task, TaskPriority, TaskStatus
from .task_queue import TaskQueue
from .task_registry import TaskRegistry
from .task_result import TaskResult

class TaskQueueManager:
    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, job_scheduler: Any = None, pipeline_orchestrator: Any = None) -> None:
        self.registry = TaskRegistry()
        self.queue = TaskQueue()
        self.dispatcher = TaskDispatcher(event_bus=event_bus, service_container=service_container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline_orchestrator)
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.job_scheduler = job_scheduler
        self.pipeline_orchestrator = pipeline_orchestrator

    def _publish(self, event_type: str, payload: dict) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.tasks", source="task_queue_manager")

    def create_task(self, name: str, action: Callable[..., Any] | None = None, *, priority: TaskPriority | int = TaskPriority.NORMAL, payload: dict | None = None, job_id: str | None = None, pipeline_id: str | None = None, workflow_name: str | None = None, max_retries: int = 0, **metadata: Any) -> Task:
        task = Task(name=name, action=action, priority=priority, payload=dict(payload or {}), job_id=job_id, pipeline_id=pipeline_id, workflow_name=workflow_name, max_retries=max_retries, metadata=dict(metadata))
        self.registry.register(task)
        self._publish("task.created", {"task_id": task.task_id, "name": task.name})
        return task

    def enqueue(self, task: Task) -> Task:
        self.registry.register(task)
        queued = self.queue.push(task)
        self._publish("task.queued", {"task_id": task.task_id, "name": task.name, "priority": int(task.priority)})
        return queued

    def enqueue_task(self, name: str, action: Callable[..., Any] | None = None, **kwargs: Any) -> Task:
        return self.enqueue(self.create_task(name, action, **kwargs))

    def cancel(self, task_id: str) -> Task:
        task = self.registry.get(task_id)
        task.cancelled = True
        task.mark(TaskStatus.CANCELLED)
        self._publish("task.cancelled", {"task_id": task.task_id, "name": task.name})
        return task

    def run_next(self) -> TaskResult | None:
        task = self.queue.pop()
        if task is None:
            return None
        return self.dispatcher.dispatch(task)

    def run_all(self) -> list[TaskResult]:
        results: list[TaskResult] = []
        while not self.queue.empty():
            result = self.run_next()
            if result is not None:
                results.append(result)
        return results

    def status(self, task_id: str) -> str:
        return self.registry.get(task_id).status.value

    def metrics(self) -> QueueMetrics:
        return QueueMetrics.from_tasks(list(self.registry.all()))

    def manifest(self) -> dict:
        return {
            "registry": self.registry.manifest(),
            "queue_length": len(self.queue),
            "metrics": self.metrics().to_dict(),
        }
