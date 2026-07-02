"""Priority job queue for NTPE Stage-09.1."""
from __future__ import annotations
import heapq
from typing import List
from .job_models import Job, JobStatus

class JobQueue:
    def __init__(self) -> None:
        self._heap: List[Job] = []

    def push(self, job: Job) -> Job:
        job.mark(JobStatus.QUEUED)
        heapq.heappush(self._heap, job)
        return job

    def pop(self) -> Job:
        if not self._heap:
            raise IndexError("job queue is empty")
        return heapq.heappop(self._heap)

    def peek(self) -> Job | None:
        return self._heap[0] if self._heap else None

    def __len__(self) -> int:
        return len(self._heap)

    def empty(self) -> bool:
        return not self._heap

    def list(self) -> list[dict]:
        return [job.to_dict() for job in sorted(self._heap)]
