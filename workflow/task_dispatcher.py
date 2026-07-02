"""Task dispatcher for NTPE Stage-09.3."""
from __future__ import annotations
from typing import Any, Dict
from .task_models import Task, TaskContext, TaskStatus
from .task_result import TaskResult

class TaskDispatcher:
    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, job_scheduler: Any = None, pipeline_orchestrator: Any = None) -> None:
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.job_scheduler = job_scheduler
        self.pipeline_orchestrator = pipeline_orchestrator

    def _publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.tasks", source="task_dispatcher")

    def dispatch(self, task: Task) -> TaskResult:
        if task.cancelled:
            task.mark(TaskStatus.CANCELLED)
            self._publish("task.cancelled", {"task_id": task.task_id, "name": task.name})
            return TaskResult(False, task.task_id, task.status, error="cancelled", attempts=task.attempts)

        while True:
            task.attempts += 1
            task.mark(TaskStatus.RUNNING)
            self._publish("task.started", {"task_id": task.task_id, "name": task.name, "attempts": task.attempts})
            try:
                context = TaskContext(
                    task_id=task.task_id,
                    job_id=task.job_id,
                    pipeline_id=task.pipeline_id,
                    workflow_name=task.workflow_name,
                    metadata=dict(task.metadata),
                )
                if task.action is not None:
                    output = task.action(context=context, payload=task.payload, services=self.service_container)
                elif task.workflow_name and self.workflow_core is not None:
                    output = self.workflow_core.execute(task.workflow_name, **task.payload)
                elif task.job_id and self.job_scheduler is not None and hasattr(self.job_scheduler, "status"):
                    output = {"job_id": task.job_id, "job_status": self.job_scheduler.status(task.job_id)}
                elif task.pipeline_id and self.pipeline_orchestrator is not None:
                    output = {"pipeline_id": task.pipeline_id}
                else:
                    output = {"task": task.name, "payload": dict(task.payload)}
                task.result = output
                task.error = None
                task.mark(TaskStatus.COMPLETED)
                self._publish("task.completed", {"task_id": task.task_id, "name": task.name, "attempts": task.attempts})
                return TaskResult(True, task.task_id, task.status, output=output, attempts=task.attempts)
            except Exception as exc:  # noqa: BLE001 - task queue isolates task failures
                task.error = str(exc)
                if task.attempts <= task.max_retries and not task.cancelled:
                    task.mark(TaskStatus.RETRYING)
                    self._publish("task.retrying", {"task_id": task.task_id, "error": str(exc), "attempts": task.attempts})
                    continue
                task.mark(TaskStatus.FAILED)
                self._publish("task.failed", {"task_id": task.task_id, "error": str(exc), "attempts": task.attempts})
                return TaskResult(False, task.task_id, task.status, error=str(exc), attempts=task.attempts)
