"""Job registry for NTPE Stage-09.1."""
from __future__ import annotations
from typing import Dict, Iterable
from .job_models import Job

class JobRegistry:
    def __init__(self) -> None:
        self._items: Dict[str, Job] = {}

    def register(self, job: Job) -> Job:
        self._items[job.job_id] = job
        return job

    def get(self, job_id: str) -> Job:
        if job_id not in self._items:
            raise KeyError(f"job not registered: {job_id}")
        return self._items[job_id]

    def all(self) -> Iterable[Job]:
        return tuple(self._items.values())

    def status(self, job_id: str) -> str:
        return self.get(job_id).status.value

    def manifest(self) -> dict:
        return {"count": len(self._items), "jobs": [job.to_dict() for job in self._items.values()]}
