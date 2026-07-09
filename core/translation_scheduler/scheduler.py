from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from typing import Any

from .collector import TranslationCollector
from .job import TranslationJob, is_retryable_error, should_retry
from .queue import TranslationQueue


class TranslationScheduler:
    def __init__(self, default_max_attempts: int = 2) -> None:
        self.queue = TranslationQueue()
        self.collector = TranslationCollector()
        self.default_max_attempts = default_max_attempts
        self.retryable_failures = 0
        self.non_retryable_failures = 0
        self.max_attempt_failures = 0
        self._started_at = time.perf_counter()

    def create_jobs(
        self,
        chunks: Sequence[str],
        packages: Sequence[Any] | dict[int, Any] | None = None,
        max_attempts: int | None = None,
    ) -> list[TranslationJob]:
        jobs: list[TranslationJob] = []
        for offset, chunk in enumerate(chunks):
            chunk_index = offset + 1
            job = TranslationJob(
                job_id=f"translation-job-{chunk_index:06d}",
                chunk_index=chunk_index,
                source_text=chunk,
                package=self._package_for(packages, offset, chunk_index),
                max_attempts=max_attempts or self.default_max_attempts,
            )
            jobs.append(self.queue.enqueue(job))
        self.collector.set_chunks_total(len(jobs))
        return jobs

    def dispatch_next(self, handler: Callable[[TranslationJob], Any]) -> TranslationJob | None:
        job = self.queue.dequeue() or self.queue.dequeue_retry()
        if job is None:
            return None
        try:
            result = handler(job)
        except Exception as exc:
            if should_retry(job, exc):
                self.retryable_failures += 1
                self.queue.mark_retry(job.job_id, exc)
            else:
                if is_retryable_error(exc):
                    self.max_attempt_failures += 1
                else:
                    self.non_retryable_failures += 1
                self.queue.mark_failed(job.job_id, exc)
                self.collector.collect_failure(job)
            return job

        self.queue.mark_done(job.job_id, result)
        self.collector.collect(job)
        return job

    def run(self, handler: Callable[[TranslationJob], Any]) -> list[TranslationJob]:
        completed: list[TranslationJob] = []
        while True:
            job = self.dispatch_next(handler)
            if job is None:
                break
            completed.append(job)
        return completed

    def attach_journal(self, journal) -> None:
        self.journal = journal

    def save_journal(self):
        if not hasattr(self, "journal"):
            raise ValueError("no resume journal attached")
        return self.journal.save_state(self)

    def performance_report(self):
        from .dashboard import PerformanceDashboard

        return PerformanceDashboard().build_report(self, getattr(self, "journal", None))

    def performance_text(self) -> str:
        from .dashboard import PerformanceDashboard

        dashboard = PerformanceDashboard()
        return dashboard.render_text(self.performance_report())

    @classmethod
    def load_from_journal(cls, path):
        from .journal import ResumeJournal

        return ResumeJournal(path).restore_scheduler()

    def summary(self) -> dict[str, int | float]:
        return {
            "jobs_total": len(self.queue.all_jobs()),
            "pending": self.queue.pending_count(),
            "running": self.queue.running_count(),
            "done": self.queue.done_count(),
            "failed": self.queue.failed_count(),
            "retry": self.queue.retry_count(),
            "retry_attempts_total": self.queue.retry_attempts_total(),
            "retryable_failures": self.retryable_failures,
            "non_retryable_failures": self.non_retryable_failures,
            "max_attempt_failures": self.max_attempt_failures,
            "collected": self.collector.collected_count(),
            "collector_failed": self.collector.failed_count(),
            "duplicates": self.collector.duplicate_count(),
            "conflicts": self.collector.conflict_count(),
            "merge_ready": self.collector.merge_ready(),
            "elapsed_seconds": round(time.perf_counter() - self._started_at, 6),
        }

    def _package_for(self, packages: Sequence[Any] | dict[int, Any] | None, offset: int, chunk_index: int) -> Any:
        if packages is None:
            return None
        if isinstance(packages, dict):
            return packages.get(chunk_index, packages.get(offset))
        return packages[offset] if offset < len(packages) else None
