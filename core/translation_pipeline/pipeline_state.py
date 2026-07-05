from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class PipelineState:
    """Execution state for a single pipeline run."""

    status: str = "created"
    current_step: str = ""
    completed_steps: list[str] = field(default_factory=list)
    failed_step: str = ""
    last_error: str = ""

    def mark_running(self, step_name: str) -> None:
        self.status = "running"
        self.current_step = step_name
        self.last_error = ""

    def mark_step_completed(self, step_name: str) -> None:
        if step_name not in self.completed_steps:
            self.completed_steps.append(step_name)
        self.current_step = ""

    def mark_completed(self) -> None:
        self.status = "success"
        self.current_step = ""

    def mark_failed(self, step_name: str, error: str) -> None:
        self.status = "failed"
        self.failed_step = step_name
        self.current_step = step_name
        self.last_error = error

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
