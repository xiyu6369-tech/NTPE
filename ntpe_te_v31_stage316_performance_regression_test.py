from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from core.translation_scheduler import PerformanceRegressionChecker


def _report(elapsed: float, avg: float, retry_attempts: int, failed: int) -> dict:
    return {
        "scheduler": {
            "jobs_total": 5,
            "pending": 0,
            "running": 0,
            "done": 5 - failed,
            "failed": failed,
            "retry": 0,
            "elapsed_seconds": elapsed,
            "merge_ready": True,
            "resume_ready": True,
        },
        "queue": {
            "pending_count": 0,
            "retry_count": 0,
            "done_count": 5 - failed,
            "failed_count": failed,
            "running_count": 0,
        },
        "retry": {
            "retry_attempts_total": retry_attempts,
            "retryable_failures": retry_attempts,
            "non_retryable_failures": 0,
            "max_attempt_failures": 0,
        },
        "collector": {
            "collected": 5 - failed,
            "collector_failed": failed,
            "duplicates": 0,
            "conflicts": 0,
            "chunks_done": 5 - failed,
            "chunks_failed": failed,
            "chunks_missing": 0,
            "merge_ready": True,
        },
        "performance": {
            "avg_job_seconds": avg,
            "max_job_seconds": avg,
            "min_job_seconds": avg,
            "throughput_jobs_per_second": 1.0,
            "estimated_remaining_seconds": 0.0,
        },
        "journal": {
            "journal_attached": True,
            "journal_path": "journal.json",
            "journal_exists": True,
            "journal_schema_version": "translation-scheduler-resume-journal-v1",
            "restore_ready": True,
        },
    }


def test_elapsed_warn_and_fail_regression() -> None:
    checker = PerformanceRegressionChecker()
    baseline = checker.create_snapshot(_report(10.0, 2.0, 1, 0), stage="TE-v3.1.5")
    warn_current = checker.create_snapshot(_report(13.0, 2.0, 1, 0), stage="TE-v3.1.6")
    fail_current = checker.create_snapshot(_report(16.0, 2.0, 1, 0), stage="TE-v3.1.6")

    assert checker.compare(baseline, warn_current)["status"] == "WARN"
    assert checker.compare(baseline, fail_current)["status"] == "FAIL"


def test_retry_delta_warn_fail_and_improvement_pass() -> None:
    checker = PerformanceRegressionChecker()
    baseline = checker.create_snapshot(_report(10.0, 2.0, 1, 0), stage="TE-v3.1.5")
    retry_warn = checker.create_snapshot(_report(10.0, 2.0, 3, 0), stage="TE-v3.1.6")
    retry_fail = checker.create_snapshot(_report(10.0, 2.0, 6, 0), stage="TE-v3.1.6")
    improved = checker.create_snapshot(_report(8.0, 1.5, 0, 0), stage="TE-v3.1.6")

    assert checker.compare(baseline, retry_warn)["status"] == "WARN"
    assert checker.compare(baseline, retry_fail)["status"] == "FAIL"
    comparison = checker.compare(baseline, improved)
    assert comparison["status"] == "PASS"
    assert comparison["summary"]["improved"] >= 1


def test_snapshot_history_and_rendering_round_trip() -> None:
    with TemporaryDirectory() as tmp_dir:
        checker = PerformanceRegressionChecker()
        baseline = checker.create_snapshot(_report(10.0, 2.0, 1, 0), stage="TE-v3.1.5", source="baseline")
        current = checker.create_snapshot(_report(13.0, 2.1, 3, 0), stage="TE-v3.1.6", source="current")
        snapshot_path = Path(tmp_dir) / "baseline.json"
        history_path = Path(tmp_dir) / "history.json"

        checker.save_snapshot(baseline, snapshot_path)
        loaded = checker.load_snapshot(snapshot_path)
        comparison = checker.compare(loaded, current)
        history = checker.append_history(comparison, history_path)
        text = checker.render_text(comparison)
        parsed = json.loads(checker.render_json(comparison))

        assert loaded["stage"] == "TE-v3.1.5"
        assert len(history) == 1
        assert checker.load_history(history_path)[0]["status"] == comparison["status"]
        assert "# NTPE Performance Regression" in text
        assert "Baseline Stage" in text
        assert "elapsed_seconds" in text
        assert parsed["current_stage"] == "TE-v3.1.6"


def main() -> int:
    test_elapsed_warn_and_fail_regression()
    test_retry_delta_warn_fail_and_improvement_pass()
    test_snapshot_history_and_rendering_round_trip()
    print("NTPE TE-v3.1 Stage-3.1.6 Performance Regression PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
