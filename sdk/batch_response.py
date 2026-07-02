"""Stage-07.3 SDK Batch response objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .batch_models import BatchProgress, BatchResult


@dataclass
class BatchResponse:
    """Structured SDK batch response."""

    ok: bool
    results: List[BatchResult] = field(default_factory=list)
    progress: BatchProgress = field(default_factory=BatchProgress)
    job_id: str = "sdk-batch-job"
    errors: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def texts(self) -> List[str]:
        return [result.text for result in self.results if result.ok]

    @property
    def failed_results(self) -> List[BatchResult]:
        return [result for result in self.results if not result.ok]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "results": [result.to_dict() for result in self.results],
            "progress": self.progress.to_dict(),
            "job_id": self.job_id,
            "errors": list(self.errors),
            "data": dict(self.data),
        }

    @classmethod
    def from_results(cls, results: List[BatchResult], progress: BatchProgress, *, job_id: str, data: Dict[str, Any] | None = None) -> "BatchResponse":
        failures = [error for result in results for error in result.errors if not result.ok]
        return cls(ok=not failures, results=list(results), progress=progress, job_id=job_id, errors=failures, data=dict(data or {}))
