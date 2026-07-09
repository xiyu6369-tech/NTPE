from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.translation_scheduler import JobStatus, ResumeJournal, TranslationScheduler


def test_resume_journal_saves_and_restores_scheduler_state() -> None:
    with TemporaryDirectory() as tmp_dir:
        journal_path = Path(tmp_dir) / "scheduler_resume.json"
        scheduler = TranslationScheduler(default_max_attempts=2)
        jobs = scheduler.create_jobs(["chunk 1", "chunk 2", "chunk 3"])

        scheduler.queue.mark_done(jobs[0].job_id, "translated 1")
        scheduler.collector.collect(jobs[0])

        scheduler.queue.mark_running(jobs[1].job_id)
        scheduler.queue.mark_retry(jobs[1].job_id, "provider timeout")

        scheduler.queue.mark_running(jobs[2].job_id)
        scheduler.queue.mark_failed(jobs[2].job_id, "authentication failed")
        scheduler.collector.collect_failure(jobs[2])

        journal = ResumeJournal(journal_path)
        snapshot = journal.save_state(scheduler)
        restored = journal.restore_scheduler()
        restored_jobs = restored.queue.all_jobs()

        assert snapshot["schema_version"]
        assert journal_path.exists()
        assert not journal_path.with_name(journal_path.name + ".tmp").exists()
        assert [job.status for job in restored_jobs] == [JobStatus.DONE, JobStatus.RETRY, JobStatus.FAILED]
        assert restored_jobs[0].result == "translated 1"
        assert restored_jobs[1].retry_count == 1
        assert restored_jobs[1].error_history == ["provider timeout"]
        assert restored_jobs[2].error == "authentication failed"
        assert restored_jobs[2].error_history == ["authentication failed"]
        assert restored.queue.pending_count() == 0
        assert restored.queue.retry_count() == 1
        assert restored.queue.failed_count() == 1
        assert restored.collector.merge_results() == "translated 1"
        assert restored.collector.build_failed_chunk_report()[0]["status"] == "FAILED"


def test_scheduler_can_attach_save_and_load_journal() -> None:
    with TemporaryDirectory() as tmp_dir:
        journal_path = Path(tmp_dir) / "attached_resume.json"
        scheduler = TranslationScheduler()
        jobs = scheduler.create_jobs(["chunk 1"])
        scheduler.queue.mark_done(jobs[0].job_id, "translated 1")
        scheduler.collector.collect(jobs[0])
        scheduler.attach_journal(ResumeJournal(journal_path))

        scheduler.save_journal()
        restored = TranslationScheduler.load_from_journal(journal_path)

        assert restored.queue.done_count() == 1
        assert restored.collector.merge_results() == "translated 1"


def main() -> int:
    test_resume_journal_saves_and_restores_scheduler_state()
    test_scheduler_can_attach_save_and_load_journal()
    print("NTPE TE-v3.1 Stage-3.1.4 Resume Journal PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
