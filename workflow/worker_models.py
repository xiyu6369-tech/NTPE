"""Worker models for NTPE 1.0 Beta Stage-09.4 Worker Runtime.

This module is additive and keeps Foundation, CLI, SDK, Integration,
and Stage-09.0~09.3 workflow contracts stable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict
import time
import uuid

WORKER_RUNTIME_VERSION = "0.9.4"
WORKER_RUNTIME_STAGE = "NTPE 1.0 Beta Stage-09.4 Worker Runtime"

class WorkerStatus(str, Enum):
    CREATED = "created"
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    TIMEOUT = "timeout"

class WorkerRuntimeStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    SHUTDOWN = "shutdown"

@dataclass
class ExecutionContext:
    worker_id: str
    task_id: str | None = None
    job_id: str | None = None
    pipeline_id: str | None = None
    workflow_name: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> "ExecutionContext":
        self.state[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "task_id": self.task_id,
            "job_id": self.job_id,
            "pipeline_id": self.pipeline_id,
            "workflow_name": self.workflow_name,
            "metadata": dict(self.metadata),
            "state": dict(self.state),
        }

@dataclass
class Worker:
    name: str
    worker_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: WorkerStatus = WorkerStatus.CREATED
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    stopped_at: float | None = None
    completed_tasks: int = 0
    failed_tasks: int = 0
    last_task_id: str | None = None
    error: str | None = None

    def mark(self, status: WorkerStatus) -> "Worker":
        self.status = status
        if status == WorkerStatus.RUNNING:
            self.started_at = time.time()
        if status in {WorkerStatus.STOPPED, WorkerStatus.FAILED, WorkerStatus.TIMEOUT}:
            self.stopped_at = time.time()
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "last_task_id": self.last_task_id,
            "error": self.error,
            "metadata": dict(self.metadata),
        }
