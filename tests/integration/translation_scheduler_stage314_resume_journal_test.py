from __future__ import annotations

from pathlib import Path

import pytest

from core.translation_scheduler import JobStatus, ResumeJournal, TranslationScheduler


def test_restore_converts_running_jobs_and_preserves_pending_failed_and_results(tmp_path: Path) -> None:
    journal_path = tmp_path / "resume.json"
    scheduler = TranslationScheduler(default_max_attempts=2)
    jobs = scheduler.create_jobs(["chunk 1", "chunk 2", "chunk 3", "chunk 4"])

    scheduler.queue.mark_done(jobs[0].job_id, "translated 1")
    scheduler.collector.collect(jobs[0])

    scheduler.queue.mark_running(jobs[1].job_id)
    jobs[1].last_error = "interrupted while running"
    jobs[1].error_history.append("interrupted while running")

    scheduler.queue.mark_failed(jobs[3].job_id, "schema error")
    scheduler.collector.collect_failure(jobs[3])

    journal = ResumeJournal(journal_path)
    journal.save_state(scheduler)
    restored = journal.restore_scheduler()
    restored_jobs = restored.queue.all_jobs()
    report = restored.collector.build_failed_chunk_report()

    assert restored_jobs[0].status == JobStatus.DONE
    assert restored_jobs[1].status == JobStatus.RETRY
    assert restored_jobs[2].status == JobStatus.PENDING
    assert restored_jobs[3].status == JobStatus.FAILED
    assert restored.queue.retry_count() == 1
    assert restored.queue.pending_count() == 1
    assert restored.collector.merge_results() == "translated 1"
    assert report[0]["chunk_index"] == 4
    assert report[0]["error"] == "schema error"


def test_restore_converts_running_at_max_attempts_to_failed(tmp_path: Path) -> None:
    journal_path = tmp_path / "resume_max_attempts.json"
    scheduler = TranslationScheduler(default_max_attempts=2)
    jobs = scheduler.create_jobs(["chunk 1"])
    scheduler.queue.mark_running(jobs[0].job_id)
    jobs[0].attempts = 2
    jobs[0].last_error = "provider timeout"
    jobs[0].error_history.append("provider timeout")

    restored = ResumeJournal(journal_path).save_state(scheduler)
    assert restored["queue_state"]["running_job_ids"] == [jobs[0].job_id]

    restored_scheduler = ResumeJournal(journal_path).restore_scheduler()
    restored_job = restored_scheduler.queue.all_jobs()[0]

    assert restored_job.status == JobStatus.FAILED
    assert restored_scheduler.queue.failed_count() == 1
    assert restored_scheduler.collector.build_failed_chunk_report()[0]["status"] == "FAILED"


def test_corrupted_journal_raises_clear_error(tmp_path: Path) -> None:
    journal_path = tmp_path / "corrupted.json"
    journal_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ValueError, match="corrupted resume journal"):
        ResumeJournal(journal_path).load_state()


def test_snapshot_validation_rejects_unknown_queue_job_ids(tmp_path: Path) -> None:
    journal = ResumeJournal(tmp_path / "bad.json")
    scheduler = TranslationScheduler()
    scheduler.create_jobs(["chunk 1"])
    snapshot = journal.build_snapshot(scheduler)
    snapshot["queue_state"]["pending_job_ids"].append("missing-job")

    with pytest.raises(ValueError, match="unknown job ids"):
        journal.validate_snapshot(snapshot)
