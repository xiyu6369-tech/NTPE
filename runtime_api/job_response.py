"""Runtime Job API response helpers for NTPE 1.0 Beta Stage-11.3."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable

from .runtime_job import RuntimeJob

RUNTIME_JOB_RESPONSE_VERSION = "1.0.0-beta.11.3"
RUNTIME_JOB_RESPONSE_STAGE = "11.3"


@dataclass(frozen=True)
class RuntimeJobListResponse:
    """Serializable job-list response."""

    jobs: tuple[RuntimeJob, ...] = field(default_factory=tuple)

    version = RUNTIME_JOB_RESPONSE_VERSION
    stage = RUNTIME_JOB_RESPONSE_STAGE

    @classmethod
    def from_jobs(cls, jobs: Iterable[RuntimeJob]) -> "RuntimeJobListResponse":
        return cls(jobs=tuple(jobs))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "jobs": [job.to_dict() for job in self.jobs],
            "count": len(self.jobs),
        }
