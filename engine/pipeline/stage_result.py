from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .utils import now_iso


@dataclass
class StageResult:
    stage: str
    status: str
    started_at: str
    ended_at: str
    message: str = ""
    warnings: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, stage: str, started_at: str, message: str = "", data: dict | None = None, warnings: list[str] | None = None):
        return cls(
            stage=stage,
            status="success",
            started_at=started_at,
            ended_at=now_iso(),
            message=message,
            warnings=warnings or [],
            data=data or {},
        )

    @classmethod
    def failed(cls, stage: str, started_at: str, message: str = "", data: dict | None = None, warnings: list[str] | None = None):
        return cls(
            stage=stage,
            status="failed",
            started_at=started_at,
            ended_at=now_iso(),
            message=message,
            warnings=warnings or [],
            data=data or {},
        )

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "message": self.message,
            "warnings": self.warnings,
            "data": self.data,
        }
