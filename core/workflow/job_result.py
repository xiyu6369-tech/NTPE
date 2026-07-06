# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobResult:
    job_id: str
    status: str
    workflow_result: Any | None = None
    attempts: int = 0
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == "completed" and self.error is None
