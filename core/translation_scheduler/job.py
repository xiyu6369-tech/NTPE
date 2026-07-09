from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    RETRY = "RETRY"


@dataclass
class TranslationJob:
    job_id: str
    chunk_index: int
    source_text: str
    package: Any = None
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    max_attempts: int = 2
    retry_count: int = 0
    last_error: str | None = None
    retryable: bool = False
    next_retry_at: datetime | None = None
    error_history: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def mark_started(self) -> None:
        if self.started_at is None:
            self.started_at = utc_now()
        self.touch()

    def mark_finished(self) -> None:
        self.finished_at = utc_now()
        if self.started_at is not None:
            self.duration_seconds = max(0.0, (self.finished_at - self.started_at).total_seconds())
        else:
            self.duration_seconds = 0.0
        self.touch()


RETRYABLE_ERROR_PATTERNS = (
    "timeout",
    "503",
    "resourceexhausted",
    "provider temporary",
    "connection reset",
)

NON_RETRYABLE_ERROR_PATTERNS = (
    "empty source",
    "invalid package",
    "api key missing",
    "authentication",
    "permission denied",
    "schema error",
)


def normalize_error(error: Any) -> str:
    return str(error)


def is_retryable_error(error: Any) -> bool:
    message = normalize_error(error).lower()
    if any(pattern in message for pattern in NON_RETRYABLE_ERROR_PATTERNS):
        return False
    return any(pattern in message for pattern in RETRYABLE_ERROR_PATTERNS)


def should_retry(job: TranslationJob, error: Any) -> bool:
    if job.status == JobStatus.DONE:
        return False
    return is_retryable_error(error) and job.attempts < job.max_attempts
