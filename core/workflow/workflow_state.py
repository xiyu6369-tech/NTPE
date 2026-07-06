# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
SKIPPED = "skipped"


@dataclass
class WorkflowState:
    status: str = PENDING
    current_step: str | None = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def start(self, step_name: str) -> None:
        self.status = RUNNING
        self.current_step = step_name

    def complete(self, step_name: str) -> None:
        if step_name not in self.completed_steps:
            self.completed_steps.append(step_name)
        self.current_step = None
        self.status = COMPLETED

    def fail(self, step_name: str) -> None:
        if step_name not in self.failed_steps:
            self.failed_steps.append(step_name)
        self.current_step = step_name
        self.status = FAILED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "current_step": self.current_step,
            "completed_steps": list(self.completed_steps),
            "failed_steps": list(self.failed_steps),
            "metadata": dict(self.metadata),
        }
