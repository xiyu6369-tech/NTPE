from __future__ import annotations
from typing import Any
from .models import DistributionResult, NodeStatus
from .scheduler import DistributedScheduler

class DistributedDispatcher:
    def __init__(self, scheduler: DistributedScheduler, *, event_bus=None, worker_runtime=None) -> None:
        self.scheduler = scheduler
        self.event_bus = event_bus
        self.worker_runtime = worker_runtime

    def _publish(self, event_type: str, payload: dict) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.distributed", source="distributed_dispatcher")

    def dispatch(self, task: Any) -> DistributionResult:
        node = self.scheduler.select_node()
        task_id = getattr(task, "task_id", None)
        if node is None:
            result = DistributionResult(False, task_id=task_id, status="failed", error="no_available_node")
            self._publish("distributed.task.failed", result.to_dict())
            return result
        node.active_tasks += 1
        node.status = NodeStatus.BUSY if node.active_tasks >= node.capacity else NodeStatus.ONLINE
        self._publish("distributed.task.distributed", {"task_id": task_id, "node_id": node.node_id})
        try:
            if self.worker_runtime is not None and hasattr(self.worker_runtime, "execute_task"):
                output = self.worker_runtime.execute_task(task)
            elif callable(getattr(task, "action", None)):
                output = task.action(getattr(task, "payload", {}))
            else:
                output = getattr(task, "payload", {})
            node.completed_tasks += 1
            result = DistributionResult(True, task_id=task_id, node_id=node.node_id, status="completed", output=output)
            self._publish("distributed.task.completed", result.to_dict())
            return result
        except Exception as exc:
            node.failed_tasks += 1
            result = DistributionResult(False, task_id=task_id, node_id=node.node_id, status="failed", error=str(exc))
            self._publish("distributed.task.failed", result.to_dict())
            return result
        finally:
            node.active_tasks = max(0, node.active_tasks - 1)
            node.status = NodeStatus.ONLINE
