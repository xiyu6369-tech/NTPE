# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from .job_priority import normalize_priority
from .job_state import JobState


@dataclass(order=True)
class JobContext:
    sort_priority: int = field(init=False, repr=False)
    sequence: int = field(default=0, compare=True)
    source_text: str = field(default="", compare=False)
    job_id: str = field(default_factory=lambda: f"job-{uuid4().hex[:12]}", compare=False)
    priority: int | str = field(default="normal", compare=False)
    metadata: dict[str, Any] = field(default_factory=dict, compare=False)
    state: JobState = field(default_factory=JobState, compare=False)

    def __post_init__(self) -> None:
        self.sort_priority = normalize_priority(self.priority)
