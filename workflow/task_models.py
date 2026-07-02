"""Task models for NTPE 1.0 Beta Stage-09.3 Task Queue.

This module is additive and keeps Stage-09.0/09.1/09.2 contracts stable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Dict
import time
import uuid

TASK_QUEUE_VERSION = "0.9.3"
TASK_QUEUE_STAGE = "NTPE 1.0 Beta Stage-09.3 Task Queue"

class TaskStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(IntEnum):
    LOW = 10
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200

@dataclass
class TaskContext:
    task_id: str
    job_id: str | None = None
    pipeline_id: str | None = None
    workflow_name: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> "TaskContext":
        self.state[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "job_id": self.job_id,
            "pipeline_id": self.pipeline_id,
            "workflow_name": self.workflow_name,
            "metadata": dict(self.metadata),
            "state": dict(self.state),
        }

@dataclass(order=True)
class Task:
    sort_index: tuple[int, float] = field(init=False, repr=False)
    name: str
    action: Callable[..., Any] | None = None
    priority: TaskPriority | int = TaskPriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str | None = None
    pipeline_id: str | None = None
    workflow_name: str | None = None
    max_retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.CREATED
    attempts: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    result: Any = None
    error: str | None = None
    cancelled: bool = False

    def __post_init__(self) -> None:
        valid_priorities = [int(p) for p in TaskPriority]
        self.priority = TaskPriority(int(self.priority)) if int(self.priority) in valid_priorities else int(self.priority)
        self.sort_index = (-int(self.priority), self.created_at)

    def mark(self, status: TaskStatus) -> "Task":
        self.status = status
        if status == TaskStatus.RUNNING:
            self.started_at = time.time()
        if status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
            self.completed_at = time.time()
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "job_id": self.job_id,
            "pipeline_id": self.pipeline_id,
            "workflow_name": self.workflow_name,
            "priority": int(self.priority),
            "status": self.status.value,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "metadata": dict(self.metadata),
        }
