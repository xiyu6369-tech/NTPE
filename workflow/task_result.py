"""Task result for NTPE Stage-09.3 Task Queue."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
from .task_models import TaskStatus

@dataclass
class TaskResult:
    ok: bool
    task_id: str
    status: TaskStatus
    output: Any = None
    error: str | None = None
    attempts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "task_id": self.task_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "attempts": self.attempts,
        }
