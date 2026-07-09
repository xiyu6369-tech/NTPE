from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from core.translation_scheduler import JobStatus, PerformanceDashboard, ResumeJournal, TranslationJob, TranslationScheduler


def test_performance_dashboard_report_text_and_json() -> None:
    with TemporaryDirectory() as tmp_dir:
        scheduler = TranslationScheduler(default_max_attempts=2)
        jobs = scheduler.create_jobs(["chunk 1", "chunk 2", "chunk 3", "chunk 4", "chunk 5"])

        scheduler.queue.mark_running(jobs[0].job_id)
        scheduler.queue.mark_done(jobs[0].job_id, "translated 1")
        scheduler.collector.collect(jobs[0])

        scheduler.queue.mark_running(jobs[1].job_id)
        scheduler.queue.mark_retry(jobs[1].job_id, "provider timeout")

        scheduler.queue.mark_running(jobs[2].job_id)
        scheduler.queue.mark_failed(jobs[2].job_id, "authentication failed")
        scheduler.collector.collect_failure(jobs[2])

        scheduler.queue.mark_running(jobs[3].job_id)
        scheduler.queue.mark_done(jobs[3].job_id, "translated 4")
        scheduler.collector.collect(jobs[3])
        duplicate = TranslationJob(job_id="job-4-duplicate", chunk_index=4, source_text="chunk 4")
        duplicate.status = JobStatus.DONE
        duplicate.result = "translated 4 changed"
        scheduler.collector.collect(duplicate)

        journal = ResumeJournal(Path(tmp_dir) / "dashboard_resume.json")
        scheduler.attach_journal(journal)
        scheduler.save_journal()

        dashboard = PerformanceDashboard()
        report = dashboard.build_report(scheduler)
        text = dashboard.render_text(report)
        parsed = json.loads(dashboard.render_json(report))

        assert report["scheduler"]["jobs_total"] == 5
        assert report["queue"]["retry_count"] == 1
        assert report["retry"]["retry_attempts_total"] == 1
        assert report["collector"]["duplicates"] == 1
        assert report["collector"]["conflicts"] == 1
        assert report["performance"]["avg_job_seconds"] is not None
        assert report["performance"]["estimated_remaining_seconds"] is not None
        assert report["journal"]["journal_attached"] is True
        assert report["journal"]["journal_exists"] is True
        assert report["journal"]["restore_ready"] is True
        assert report["scheduler"]["resume_ready"] is True
        assert "# NTPE Translation Scheduler Performance" in text
        assert "Jobs Total" in text
        assert "Resume Ready" in text
        assert parsed["scheduler"]["jobs_total"] == 5


def test_scheduler_performance_helpers() -> None:
    scheduler = TranslationScheduler()
    jobs = scheduler.create_jobs(["chunk 1"])
    scheduler.queue.mark_running(jobs[0].job_id)
    scheduler.queue.mark_done(jobs[0].job_id, "translated 1")
    scheduler.collector.collect(jobs[0])

    report = scheduler.performance_report()
    text = scheduler.performance_text()

    assert report["scheduler"]["done"] == 1
    assert "Done" in text


def main() -> int:
    test_performance_dashboard_report_text_and_json()
    test_scheduler_performance_helpers()
    print("NTPE TE-v3.1 Stage-3.1.5 Performance Dashboard PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
