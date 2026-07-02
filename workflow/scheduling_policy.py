"""Scheduling policy for NTPE Stage-09.1."""
from __future__ import annotations
from dataclasses import dataclass
from .job_models import Job, JobPriority

@dataclass
class SchedulingPolicy:
    default_priority: JobPriority = JobPriority.NORMAL
    default_max_retries: int = 0
    allow_retry: bool = True
    allow_cancel: bool = True

    def normalize(self, job: Job) -> Job:
        if job.priority is None:
            job.priority = self.default_priority
        if job.max_retries < 0:
            job.max_retries = self.default_max_retries
        return job

    def should_retry(self, job: Job) -> bool:
        return self.allow_retry and job.attempts <= job.max_retries and not job.cancelled
