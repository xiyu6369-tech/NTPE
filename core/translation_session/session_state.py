from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class SessionState:
    """Additive NTPE 1.2 translation session state container."""

    status: str = "created"
    progress_current: int = 0
    progress_total: int = 0
    resume_token: str = ""
    last_error: str = ""

    @property
    def progress_percent(self) -> float:
        if self.progress_total <= 0:
            return 0.0
        return round((self.progress_current / self.progress_total) * 100.0, 2)

    def mark_running(self) -> None:
        self.status = "running"

    def mark_completed(self) -> None:
        self.status = "success"
        if self.progress_total:
            self.progress_current = self.progress_total

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.last_error = error

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["progress_percent"] = self.progress_percent
        return data
