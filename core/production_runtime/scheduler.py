"""NTPE 1.0 Beta Stage-01 Production Runtime scheduler."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class RuntimeTask:
    task_id: str = field(default_factory=lambda: f"task-{uuid.uuid4().hex[:10]}")
    segment: Any = None
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {"task_id": self.task_id, "segment": self.segment, "payload": dict(self.payload), "status": self.status}


class RuntimeScheduler:
    """Deterministic in-process FIFO scheduler for segment jobs."""

    version = "ntpe-1.0-beta-stage-01"

    def __init__(self):
        self._queue: List[RuntimeTask] = []
        self._completed: List[RuntimeTask] = []

    def submit(self, segment: Any = None, payload: Optional[Dict[str, Any]] = None, task_id: Optional[str] = None) -> RuntimeTask:
        task = RuntimeTask(task_id=task_id or f"task-{uuid.uuid4().hex[:10]}", segment=segment, payload=dict(payload or {}))
        self._queue.append(task)
        return task

    def submit_many(self, segments: Iterable[Any]) -> List[RuntimeTask]:
        return [self.submit(segment=segment) for segment in segments]

    def next_task(self) -> Optional[RuntimeTask]:
        if not self._queue:
            return None
        task = self._queue.pop(0)
        task.status = "running"
        return task

    def complete(self, task: RuntimeTask) -> RuntimeTask:
        task.status = "completed"
        self._completed.append(task)
        return task

    def pending_count(self) -> int:
        return len(self._queue)

    def completed_count(self) -> int:
        return len(self._completed)

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "production_runtime_scheduler",
            "version": self.version,
            "pending": self.pending_count(),
            "completed": self.completed_count(),
        }


__all__ = ["RuntimeScheduler", "RuntimeTask"]
