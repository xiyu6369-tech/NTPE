"""Job models for NTPE 1.0 Beta Stage-09.1 Job Scheduler.

This module is additive and does not alter Stage-09.0 Workflow Core contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, Optional
import time
import uuid

JOB_SCHEDULER_VERSION = "0.9.1"
JOB_SCHEDULER_STAGE = "NTPE 1.0 Beta Stage-09.1 Job Scheduler"

class JobStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"

class JobPriority(IntEnum):
    LOW = 10
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200

@dataclass
class JobContext:
    job_id: str
    workflow_name: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> "JobContext":
        self.state[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

@dataclass(order=True)
class Job:
    sort_index: tuple[int, float] = field(init=False, repr=False)
    name: str
    action: Callable[..., Any] | None = None
    priority: JobPriority | int = JobPriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str | None = None
    max_retries: int = 0
    timeout_seconds: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.CREATED
    attempts: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    result: Any = None
    error: str | None = None
    cancelled: bool = False

    def __post_init__(self) -> None:
        self.priority = JobPriority(int(self.priority)) if int(self.priority) in [int(p) for p in JobPriority] else int(self.priority)
        # heapq is min-first; negative priority yields high priority first.
        self.sort_index = (-int(self.priority), self.created_at)

    def mark(self, status: JobStatus) -> "Job":
        self.status = status
        if status == JobStatus.RUNNING:
            self.started_at = time.time()
        if status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMEOUT}:
            self.completed_at = time.time()
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "workflow_name": self.workflow_name,
            "priority": int(self.priority),
            "status": self.status.value,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "metadata": dict(self.metadata),
        }

@dataclass
class JobResult:
    ok: bool
    job_id: str
    status: JobStatus
    output: Any = None
    error: str | None = None
    attempts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "job_id": self.job_id, "status": self.status.value, "output": self.output, "error": self.error, "attempts": self.attempts}
