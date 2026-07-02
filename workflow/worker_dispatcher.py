"""Worker task dispatcher for NTPE Stage-09.4."""
from __future__ import annotations
from typing import Any, Dict
import time

from .task_models import Task, TaskStatus
from .task_result import TaskResult
from .worker_models import ExecutionContext, Worker, WorkerStatus

class WorkerDispatcher:
    def __init__(self, *, event_bus: Any = None, service_container: Any = None, task_dispatcher: Any = None) -> None:
        self.event_bus = event_bus
        self.service_container = service_container
        self.task_dispatcher = task_dispatcher

    def _publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.workers", source="worker_dispatcher")

    def dispatch(self, worker: Worker, task: Task, *, timeout: float | None = None) -> TaskResult:
        worker.mark(WorkerStatus.RUNNING)
        worker.last_task_id = task.task_id
        self._publish("worker.task.started", {"worker_id": worker.worker_id, "task_id": task.task_id, "name": task.name})
        started = time.time()
        try:
            if timeout is not None and timeout <= 0:
                raise TimeoutError("worker task timeout")

            if self.task_dispatcher is not None:
                result = self.task_dispatcher.dispatch(task)
            else:
                task.attempts += 1
                task.mark(TaskStatus.RUNNING)
                context = ExecutionContext(
                    worker_id=worker.worker_id,
                    task_id=task.task_id,
                    job_id=task.job_id,
                    pipeline_id=task.pipeline_id,
                    workflow_name=task.workflow_name,
                    metadata=dict(task.metadata),
                )
                output = task.action(context=context, payload=task.payload, services=self.service_container) if task.action else dict(task.payload)
                task.result = output
                task.error = None
                task.mark(TaskStatus.COMPLETED)
                result = TaskResult(True, task.task_id, task.status, output=output, attempts=task.attempts)

            if timeout is not None and time.time() - started > timeout:
                task.error = "worker task timeout"
                task.mark(TaskStatus.FAILED)
                worker.error = task.error
                worker.failed_tasks += 1
                worker.mark(WorkerStatus.TIMEOUT)
                self._publish("worker.timeout", {"worker_id": worker.worker_id, "task_id": task.task_id})
                return TaskResult(False, task.task_id, task.status, error=task.error, attempts=task.attempts)

            if result.ok:
                worker.completed_tasks += 1
                worker.error = None
                worker.mark(WorkerStatus.IDLE)
                self._publish("worker.task.completed", {"worker_id": worker.worker_id, "task_id": task.task_id})
            else:
                worker.failed_tasks += 1
                worker.error = result.error
                worker.mark(WorkerStatus.FAILED)
                self._publish("worker.task.failed", {"worker_id": worker.worker_id, "task_id": task.task_id, "error": result.error})
            return result
        except Exception as exc:  # noqa: BLE001 - worker isolates task failures
            task.error = str(exc)
            task.mark(TaskStatus.FAILED)
            worker.error = str(exc)
            worker.failed_tasks += 1
            worker.mark(WorkerStatus.FAILED)
            self._publish("worker.task.failed", {"worker_id": worker.worker_id, "task_id": task.task_id, "error": str(exc)})
            return TaskResult(False, task.task_id, task.status, error=str(exc), attempts=task.attempts)
