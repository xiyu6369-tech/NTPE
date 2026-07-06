# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from time import time


JOB_PENDING = "pending"
JOB_RUNNING = "running"
JOB_COMPLETED = "completed"
JOB_FAILED = "failed"
JOB_PAUSED = "paused"
JOB_CANCELLED = "cancelled"


@dataclass
class JobState:
    status: str = JOB_PENDING
    attempts: int = 0
    max_retries: int = 2
    progress: float = 0.0
    created_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)
    error: str | None = None

    @property
    def can_retry(self) -> bool:
        return self.attempts <= self.max_retries

    def mark(self, status: str, *, progress: float | None = None, error: str | None = None) -> None:
        self.status = status
        if progress is not None:
            self.progress = max(0.0, min(1.0, progress))
        self.error = error
        self.updated_at = time()
