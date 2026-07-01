from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
import time


@dataclass
class ExecutorResult:
    executor_id: str
    job_id: str
    segment_id: str
    status: str = "completed"
    output_text: str = ""
    error: Optional[str] = None
    model: str = "mock"
    attempts: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def create_executor_result(
    job_id: str,
    segment_id: str,
    output_text: str = "",
    status: str = "completed",
    error: Optional[str] = None,
    model: str = "mock",
    attempts: int = 1,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return ExecutorResult(
        executor_id=f"executor:{job_id}:{segment_id}",
        job_id=job_id,
        segment_id=segment_id,
        status=status,
        output_text=output_text,
        error=error,
        model=model,
        attempts=attempts,
        metadata=metadata or {},
    ).to_dict()


def validate_executor_result(result: Dict[str, Any]) -> bool:
    if not isinstance(result, dict):
        return False
    required = ["executor_id", "job_id", "segment_id", "status", "attempts"]
    if any(k not in result for k in required):
        return False
    if result["status"] not in {"completed", "failed", "skipped"}:
        return False
    if not isinstance(result.get("attempts"), int) or result["attempts"] < 0:
        return False
    return True
