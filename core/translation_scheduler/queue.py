from __future__ import annotations

from collections import OrderedDict
from datetime import timedelta

from .job import JobStatus, TranslationJob, is_retryable_error, utc_now


class TranslationQueue:
    def __init__(self) -> None:
        self._jobs: OrderedDict[str, TranslationJob] = OrderedDict()

    def enqueue(self, job: TranslationJob) -> TranslationJob:
        if job.job_id in self._jobs:
            raise ValueError(f"duplicate translation job_id: {job.job_id}")
        self._jobs[job.job_id] = job
        job.status = JobStatus.PENDING
        job.touch()
        return job

    def dequeue(self) -> TranslationJob | None:
        for job in self._jobs.values():
            if job.status == JobStatus.PENDING:
                return self.mark_running(job.job_id)
        return None

    def dequeue_retry(self) -> TranslationJob | None:
        for job in self._jobs.values():
            if job.status == JobStatus.RETRY:
                return self.mark_running(job.job_id)
        return None

    def mark_running(self, job_id: str) -> TranslationJob:
        job = self._get(job_id)
        if job.status != JobStatus.RUNNING:
            job.attempts += 1
        job.status = JobStatus.RUNNING
        job.mark_started()
        return job

    def mark_done(self, job_id: str, result) -> TranslationJob:
        job = self._get(job_id)
        job.status = JobStatus.DONE
        job.result = result
        job.error = None
        job.last_error = None
        job.retryable = False
        job.mark_finished()
        return job

    def mark_failed(self, job_id: str, error) -> TranslationJob:
        job = self._get(job_id)
        job.status = JobStatus.FAILED
        message = str(error)
        job.error = message
        job.last_error = message
        job.retryable = is_retryable_error(error)
        job.next_retry_at = None
        job.error_history.append(message)
        job.mark_finished()
        return job

    def mark_retry(self, job_id: str, error) -> TranslationJob:
        job = self._get(job_id)
        if job.status == JobStatus.DONE:
            raise ValueError(f"done translation job cannot be retried: {job_id}")
        message = str(error)
        job.status = JobStatus.RETRY
        job.error = message
        job.last_error = message
        job.retryable = True
        job.retry_count += 1
        job.next_retry_at = utc_now() + timedelta(seconds=0)
        job.error_history.append(message)
        job.touch()
        return job

    def pending_count(self) -> int:
        return self._count(JobStatus.PENDING)

    def running_count(self) -> int:
        return self._count(JobStatus.RUNNING)

    def done_count(self) -> int:
        return self._count(JobStatus.DONE)

    def failed_count(self) -> int:
        return self._count(JobStatus.FAILED)

    def retry_count(self) -> int:
        return self._count(JobStatus.RETRY)

    def retry_attempts_total(self) -> int:
        return sum(job.retry_count for job in self._jobs.values())

    def has_retry_jobs(self) -> bool:
        return self.retry_count() > 0

    def all_jobs(self) -> list[TranslationJob]:
        return list(self._jobs.values())

    def _count(self, status: JobStatus) -> int:
        return sum(1 for job in self._jobs.values() if job.status == status)

    def _get(self, job_id: str) -> TranslationJob:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise KeyError(f"unknown translation job_id: {job_id}") from exc
