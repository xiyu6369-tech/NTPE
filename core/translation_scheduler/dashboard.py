from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from .collector import TranslationCollector
from .job import JobStatus
from .journal import SCHEMA_VERSION, ResumeJournal
from .queue import TranslationQueue


class PerformanceDashboard:
    def collect_scheduler_metrics(self, scheduler) -> dict[str, Any]:
        summary = scheduler.summary()
        return {
            "jobs_total": summary["jobs_total"],
            "pending": summary["pending"],
            "running": summary["running"],
            "done": summary["done"],
            "failed": summary["failed"],
            "retry": summary["retry"],
            "elapsed_seconds": summary["elapsed_seconds"],
            "merge_ready": summary["merge_ready"],
            "resume_ready": bool(getattr(scheduler, "journal", None)),
        }

    def collect_queue_metrics(self, queue: TranslationQueue) -> dict[str, int]:
        return {
            "pending_count": queue.pending_count(),
            "retry_count": queue.retry_count(),
            "done_count": queue.done_count(),
            "failed_count": queue.failed_count(),
            "running_count": queue.running_count(),
        }

    def collect_collector_metrics(self, collector: TranslationCollector) -> dict[str, Any]:
        manifest = collector.build_manifest()
        return {
            "collected": collector.collected_count(),
            "collector_failed": collector.failed_count(),
            "duplicates": collector.duplicate_count(),
            "conflicts": collector.conflict_count(),
            "chunks_done": manifest["chunks_done"],
            "chunks_failed": manifest["chunks_failed"],
            "chunks_missing": manifest["chunks_missing"],
            "merge_ready": manifest["merge_ready"],
        }

    def collect_journal_metrics(self, journal: ResumeJournal | None = None) -> dict[str, Any]:
        if journal is None:
            return {
                "journal_attached": False,
                "journal_path": None,
                "journal_exists": False,
                "journal_schema_version": None,
                "restore_ready": False,
            }
        journal_path = Path(journal.journal_path)
        exists = journal_path.exists()
        schema_version = None
        restore_ready = False
        if exists:
            try:
                snapshot = journal.load_state()
                schema_version = snapshot.get("schema_version")
                restore_ready = True
            except ValueError:
                restore_ready = False
        return {
            "journal_attached": True,
            "journal_path": str(journal_path),
            "journal_exists": exists,
            "journal_schema_version": schema_version,
            "restore_ready": restore_ready,
        }

    def build_report(self, scheduler, journal: ResumeJournal | None = None) -> dict[str, Any]:
        attached_journal = journal if journal is not None else getattr(scheduler, "journal", None)
        scheduler_metrics = self.collect_scheduler_metrics(scheduler)
        journal_metrics = self.collect_journal_metrics(attached_journal)
        scheduler_metrics["resume_ready"] = journal_metrics["restore_ready"]
        return {
            "scheduler": scheduler_metrics,
            "queue": self.collect_queue_metrics(scheduler.queue),
            "retry": self._retry_metrics(scheduler),
            "collector": self.collect_collector_metrics(scheduler.collector),
            "performance": self._performance_metrics(scheduler),
            "journal": journal_metrics,
        }

    def render_text(self, report: dict[str, Any]) -> str:
        scheduler = report["scheduler"]
        retry = report["retry"]
        collector = report["collector"]
        performance = report["performance"]
        lines = [
            "# NTPE Translation Scheduler Performance",
            "",
            f"{'Jobs Total':18}{scheduler['jobs_total']}",
            f"{'Done':18}{scheduler['done']}",
            f"{'Failed':18}{scheduler['failed']}",
            f"{'Retry':18}{scheduler['retry']}",
            f"{'Pending':18}{scheduler['pending']}",
            "",
            f"{'Retry Attempts':18}{retry['retry_attempts_total']}",
            f"{'Duplicates':18}{collector['duplicates']}",
            f"{'Conflicts':18}{collector['conflicts']}",
            "",
            f"{'Avg Job Seconds':18}{self._format_seconds(performance['avg_job_seconds'])}",
            f"{'Elapsed Seconds':18}{self._format_seconds(scheduler['elapsed_seconds'])}",
            f"{'Merge Ready':18}{scheduler['merge_ready']}",
            f"{'Resume Ready':18}{scheduler['resume_ready']}",
        ]
        return "\n".join(lines)

    def render_json(self, report: dict[str, Any]) -> str:
        return json.dumps(report, ensure_ascii=False, indent=2)

    def _retry_metrics(self, scheduler) -> dict[str, int]:
        summary = scheduler.summary()
        return {
            "retry_attempts_total": summary["retry_attempts_total"],
            "retryable_failures": summary["retryable_failures"],
            "non_retryable_failures": summary["non_retryable_failures"],
            "max_attempt_failures": summary["max_attempt_failures"],
        }

    def _performance_metrics(self, scheduler) -> dict[str, float | None]:
        jobs = scheduler.queue.all_jobs()
        durations = [
            float(job.duration_seconds)
            for job in jobs
            if job.duration_seconds is not None and job.status in {JobStatus.DONE, JobStatus.FAILED}
        ]
        avg_duration = mean(durations) if durations else None
        remaining_jobs = scheduler.queue.pending_count() + scheduler.queue.retry_count()
        elapsed = scheduler.summary()["elapsed_seconds"]
        finished_count = scheduler.queue.done_count() + scheduler.queue.failed_count()
        return {
            "avg_job_seconds": avg_duration,
            "max_job_seconds": max(durations) if durations else None,
            "min_job_seconds": min(durations) if durations else None,
            "throughput_jobs_per_second": (finished_count / elapsed) if elapsed else None,
            "estimated_remaining_seconds": (avg_duration * remaining_jobs) if avg_duration is not None else None,
        }

    def _format_seconds(self, value: float | None) -> str:
        if value is None:
            return "None"
        return f"{value:.3f}"
