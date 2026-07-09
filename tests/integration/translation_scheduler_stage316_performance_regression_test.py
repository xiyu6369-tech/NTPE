from __future__ import annotations

from pathlib import Path

from core.translation_scheduler import PerformanceDashboard, PerformanceRegressionChecker, TranslationScheduler


def _completed_scheduler(duration: float, retry_attempts: int = 0, failed: int = 0) -> TranslationScheduler:
    scheduler = TranslationScheduler()
    jobs = scheduler.create_jobs(["chunk 1", "chunk 2", "chunk 3"])
    for index, job in enumerate(jobs):
        scheduler.queue.mark_running(job.job_id)
        if index < failed:
            scheduler.queue.mark_failed(job.job_id, "schema error")
            scheduler.collector.collect_failure(job)
        else:
            scheduler.queue.mark_done(job.job_id, f"translated {job.chunk_index}")
            scheduler.collector.collect(job)
        job.duration_seconds = duration
    for job in jobs[:retry_attempts]:
        job.retry_count = 1
    return scheduler


def test_dashboard_snapshot_regression_compare_and_history(tmp_path: Path) -> None:
    dashboard = PerformanceDashboard()
    checker = PerformanceRegressionChecker()
    baseline_scheduler = _completed_scheduler(duration=1.0)
    current_scheduler = _completed_scheduler(duration=1.3, retry_attempts=2)

    baseline_report = dashboard.build_report(baseline_scheduler)
    current_report = dashboard.build_report(current_scheduler)
    baseline_report["scheduler"]["elapsed_seconds"] = 10.0
    current_report["scheduler"]["elapsed_seconds"] = 13.0
    baseline = checker.create_snapshot(baseline_report, stage="TE-v3.1.5", source="dashboard")
    current = checker.create_snapshot(current_report, stage="TE-v3.1.6", source="dashboard")

    comparison = checker.compare(baseline, current)
    history = checker.append_history(comparison, tmp_path / "history.json")

    assert comparison["status"] == "WARN"
    assert comparison["baseline_stage"] == "TE-v3.1.5"
    assert comparison["current_stage"] == "TE-v3.1.6"
    assert any(check["metric"] == "elapsed_seconds" and check["status"] == "WARN" for check in comparison["checks"])
    assert len(history) == 1
    assert checker.load_history(tmp_path / "history.json")[0]["status"] == "WARN"


def test_failed_delta_regression_from_dashboard_report() -> None:
    dashboard = PerformanceDashboard()
    checker = PerformanceRegressionChecker()
    baseline = checker.create_snapshot(dashboard.build_report(_completed_scheduler(duration=1.0, failed=0)), stage="TE-v3.1.5")
    current = checker.create_snapshot(dashboard.build_report(_completed_scheduler(duration=1.0, failed=2)), stage="TE-v3.1.6")

    comparison = checker.compare(baseline, current)

    assert comparison["status"] == "FAIL"
    assert any(check["metric"] == "failed" and check["status"] == "FAIL" for check in comparison["checks"])
