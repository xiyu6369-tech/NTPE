from __future__ import annotations

import json
from pathlib import Path

from core.translation_scheduler import JobStatus, PerformanceDashboard, ResumeJournal, TranslationJob, TranslationScheduler


def test_dashboard_integrates_scheduler_retry_collector_and_journal(tmp_path: Path) -> None:
    scheduler = TranslationScheduler(default_max_attempts=2)
    jobs = scheduler.create_jobs(["chunk 1", "chunk 2", "chunk 3", "chunk 4", "chunk 5"])

    scheduler.queue.mark_running(jobs[0].job_id)
    scheduler.queue.mark_done(jobs[0].job_id, "translated 1")
    scheduler.collector.collect(jobs[0])

    scheduler.queue.mark_running(jobs[1].job_id)
    scheduler.queue.mark_failed(jobs[1].job_id, "schema error")
    scheduler.collector.collect_failure(jobs[1])

    scheduler.queue.mark_running(jobs[2].job_id)
    scheduler.queue.mark_done(jobs[2].job_id, "translated 3")
    scheduler.collector.collect(jobs[2])

    scheduler.queue.mark_running(jobs[3].job_id)
    scheduler.queue.mark_done(jobs[3].job_id, "translated 4")
    scheduler.collector.collect(jobs[3])
    duplicate = TranslationJob(job_id="job-4-duplicate", chunk_index=4, source_text="chunk 4")
    duplicate.status = JobStatus.DONE
    duplicate.result = "translated 4 conflict"
    scheduler.collector.collect(duplicate)

    journal = ResumeJournal(tmp_path / "performance_resume.json")
    scheduler.attach_journal(journal)
    scheduler.save_journal()

    dashboard = PerformanceDashboard()
    report = dashboard.build_report(scheduler, journal)

    assert report["journal"]["journal_exists"] is True
    assert report["journal"]["restore_ready"] is True
    assert report["collector"]["collector_failed"] == 1
    assert report["collector"]["chunks_missing"] == 1
    assert report["collector"]["duplicates"] == 1
    assert report["collector"]["conflicts"] == 1
    assert report["collector"]["merge_ready"] is False
    assert report["scheduler"]["merge_ready"] is False
    assert report["scheduler"]["resume_ready"] is True
    assert scheduler.collector.merge_results() == "translated 1\ntranslated 3\ntranslated 4"
    assert json.loads(dashboard.render_json(report))["journal"]["journal_exists"] is True


def test_dashboard_without_journal_reports_not_resume_ready() -> None:
    scheduler = TranslationScheduler()
    scheduler.create_jobs(["chunk 1"])
    report = PerformanceDashboard().build_report(scheduler)

    assert report["journal"]["journal_attached"] is False
    assert report["journal"]["journal_exists"] is False
    assert report["journal"]["restore_ready"] is False
    assert report["scheduler"]["resume_ready"] is False
