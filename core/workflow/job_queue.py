# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager
# =====================================================

from __future__ import annotations

import heapq
from itertools import count
from typing import Iterable

from .job_context import JobContext
from .job_events import JOB_ENQUEUED, JobEventBus
from .job_exceptions import JobQueueError


class JobQueue:
    """Priority queue for workflow jobs. Lower priority value runs first."""

    def __init__(self, event_bus: JobEventBus | None = None) -> None:
        self._items: list[JobContext] = []
        self._sequence = count(1)
        self.event_bus = event_bus or JobEventBus()
        self.paused = False

    def put(self, job: JobContext | str, *, priority: int | str | None = None) -> JobContext:
        if isinstance(job, str):
            job = JobContext(source_text=job, priority=priority or "normal")
        elif priority is not None:
            job.priority = priority
            job.__post_init__()
        job.sequence = next(self._sequence)
        heapq.heappush(self._items, job)
        self.event_bus.emit(JOB_ENQUEUED, job_id=job.job_id, priority=job.sort_priority)
        return job

    def extend(self, jobs: Iterable[JobContext | str]) -> list[JobContext]:
        return [self.put(job) for job in jobs]

    def get(self) -> JobContext:
        if self.paused:
            raise JobQueueError("job queue is paused")
        if not self._items:
            raise JobQueueError("job queue is empty")
        return heapq.heappop(self._items)

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def __len__(self) -> int:
        return len(self._items)

    def empty(self) -> bool:
        return not self._items
