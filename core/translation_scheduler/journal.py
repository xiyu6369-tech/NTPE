from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .collector import TranslationCollector
from .job import JobStatus, TranslationJob, utc_now
from .queue import TranslationQueue
from .scheduler import TranslationScheduler


SCHEMA_VERSION = "translation-scheduler-resume-journal-v1"


class ResumeJournal:
    def __init__(self, journal_path: str | Path) -> None:
        self.journal_path = Path(journal_path)

    def save_state(self, scheduler: TranslationScheduler) -> dict[str, Any]:
        snapshot = self.build_snapshot(scheduler)
        self.validate_snapshot(snapshot)
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.journal_path.with_name(self.journal_path.name + ".tmp")
        tmp_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        json.loads(tmp_path.read_text(encoding="utf-8"))
        os.replace(tmp_path, self.journal_path)
        return snapshot

    def load_state(self) -> dict[str, Any]:
        try:
            snapshot = json.loads(self.journal_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"corrupted resume journal: {self.journal_path}") from exc
        except OSError as exc:
            raise ValueError(f"cannot read resume journal: {self.journal_path}") from exc
        self.validate_snapshot(snapshot)
        return snapshot

    def restore_scheduler(self) -> TranslationScheduler:
        snapshot = self.load_state()
        scheduler = TranslationScheduler()
        scheduler.attach_journal(self)
        scheduler.queue = TranslationQueue()
        chunks_total = int(snapshot.get("collector_manifest", {}).get("chunks_total", len(snapshot["jobs"])))
        scheduler.collector = TranslationCollector(chunks_total=chunks_total)
        scheduler._started_at = time.perf_counter()

        for job_data in snapshot["jobs"]:
            job = self._job_from_snapshot(job_data)
            self._normalize_restored_status(job)
            scheduler.queue._jobs[job.job_id] = job
            if job.status == JobStatus.DONE:
                scheduler.collector.collect(job)
            elif job.status == JobStatus.FAILED:
                scheduler.collector.collect_failure(job)

        scheduler.collector.restore_audit(snapshot.get("collector_manifest", {}))
        return scheduler

    def build_snapshot(self, scheduler: TranslationScheduler) -> dict[str, Any]:
        now = utc_now().isoformat()
        jobs = [self._job_to_snapshot(job) for job in scheduler.queue.all_jobs()]
        return {
            "schema_version": SCHEMA_VERSION,
            "created_at": now,
            "updated_at": now,
            "scheduler_summary": scheduler.summary(),
            "jobs": jobs,
            "collector_manifest": scheduler.collector.build_manifest(),
            "failed_chunk_report": scheduler.collector.build_failed_chunk_report(),
            "queue_state": self._queue_state(scheduler.queue.all_jobs()),
        }

    def validate_snapshot(self, snapshot: dict[str, Any]) -> bool:
        if not isinstance(snapshot, dict):
            raise ValueError("resume journal snapshot must be a dict")
        if not snapshot.get("schema_version"):
            raise ValueError("resume journal schema_version is required")
        jobs = snapshot.get("jobs")
        if not isinstance(jobs, list):
            raise ValueError("resume journal jobs must be a list")
        job_ids = [job.get("job_id") for job in jobs if isinstance(job, dict)]
        if len(job_ids) != len(set(job_ids)):
            raise ValueError("resume journal contains duplicate job_id values")
        chunk_indexes = [job.get("chunk_index") for job in jobs if isinstance(job, dict)]
        duplicate_chunks = len(chunk_indexes) != len(set(chunk_indexes))
        duplicates = snapshot.get("collector_manifest", {}).get("duplicates", [])
        if duplicate_chunks and not duplicates:
            raise ValueError("resume journal contains duplicate chunk_index values without duplicate records")
        known_job_ids = set(job_ids)
        queue_state = snapshot.get("queue_state")
        if not isinstance(queue_state, dict):
            raise ValueError("resume journal queue_state must be a dict")
        for key in ("pending_job_ids", "retry_job_ids", "running_job_ids", "done_job_ids", "failed_job_ids"):
            ids = queue_state.get(key)
            if not isinstance(ids, list):
                raise ValueError(f"resume journal queue_state.{key} must be a list")
            unknown = [job_id for job_id in ids if job_id not in known_job_ids]
            if unknown:
                raise ValueError(f"resume journal queue_state.{key} references unknown job ids")
        if not isinstance(snapshot.get("collector_manifest"), dict):
            raise ValueError("resume journal collector_manifest must be a dict")
        return True

    def _queue_state(self, jobs: list[TranslationJob]) -> dict[str, list[str]]:
        return {
            "pending_job_ids": [job.job_id for job in jobs if job.status == JobStatus.PENDING],
            "retry_job_ids": [job.job_id for job in jobs if job.status == JobStatus.RETRY],
            "running_job_ids": [job.job_id for job in jobs if job.status == JobStatus.RUNNING],
            "done_job_ids": [job.job_id for job in jobs if job.status == JobStatus.DONE],
            "failed_job_ids": [job.job_id for job in jobs if job.status == JobStatus.FAILED],
        }

    def _job_to_snapshot(self, job: TranslationJob) -> dict[str, Any]:
        return {
            "job_id": job.job_id,
            "chunk_index": job.chunk_index,
            "source_text": job.source_text,
            "package": job.package,
            "status": job.status.value,
            "attempts": job.attempts,
            "max_attempts": job.max_attempts,
            "retry_count": job.retry_count,
            "retryable": job.retryable,
            "result": job.result,
            "error": job.error,
            "last_error": job.last_error,
            "error_history": list(job.error_history),
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "next_retry_at": job.next_retry_at.isoformat() if job.next_retry_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "duration_seconds": job.duration_seconds,
        }

    def _job_from_snapshot(self, data: dict[str, Any]) -> TranslationJob:
        job = TranslationJob(
            job_id=data["job_id"],
            chunk_index=int(data["chunk_index"]),
            source_text=data.get("source_text", ""),
            package=data.get("package"),
            status=JobStatus(data.get("status", JobStatus.PENDING.value)),
            attempts=int(data.get("attempts", 0)),
            max_attempts=int(data.get("max_attempts", 2)),
            retry_count=int(data.get("retry_count", 0)),
            retryable=bool(data.get("retryable", False)),
            result=data.get("result"),
            error=data.get("error"),
            last_error=data.get("last_error"),
            error_history=list(data.get("error_history", [])),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )
        if data.get("next_retry_at"):
            job.next_retry_at = self._parse_datetime(data["next_retry_at"])
        if data.get("started_at"):
            job.started_at = self._parse_datetime(data["started_at"])
        if data.get("finished_at"):
            job.finished_at = self._parse_datetime(data["finished_at"])
        job.duration_seconds = data.get("duration_seconds")
        return job

    def _normalize_restored_status(self, job: TranslationJob) -> None:
        if job.status != JobStatus.RUNNING:
            return
        if job.attempts < job.max_attempts:
            job.status = JobStatus.RETRY
            job.retryable = True
            if not job.last_error:
                job.last_error = "restored running job"
        else:
            job.status = JobStatus.FAILED
            job.error = job.error or job.last_error or "running job exceeded max attempts during restore"
            job.last_error = job.error
            if not job.error_history:
                job.error_history.append(job.error)

    def _parse_datetime(self, value: str | None) -> datetime:
        if not value:
            return utc_now()
        return datetime.fromisoformat(value)
