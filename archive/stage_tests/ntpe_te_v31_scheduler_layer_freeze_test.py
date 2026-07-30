from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from core.translation_scheduler import (
    PerformanceDashboard,
    PerformanceRegressionChecker,
    ResumeJournal,
    SCHEDULER_LAYER_RELEASE_ID,
    SCHEDULER_LAYER_STATUS,
    TranslationCollector,
    TranslationJob,
    TranslationQueue,
    TranslationScheduler,
)
from core.translation_scheduler.job import JobStatus


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v31_scheduler_layer_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_scheduler_layer_imports_and_components() -> None:
    module = importlib.import_module("core.translation_scheduler")
    scheduler = TranslationScheduler()
    job = TranslationJob(job_id="freeze-job-1", chunk_index=1, source_text="source")
    queue = TranslationQueue()
    queue.enqueue(job)
    dequeued = queue.dequeue()
    queue.mark_done(job.job_id, "translated")
    collector = TranslationCollector(chunks_total=1)
    collector.collect(job)

    assert module.SCHEDULER_LAYER_RELEASE_ID == SCHEDULER_LAYER_RELEASE_ID
    assert SCHEDULER_LAYER_STATUS == "frozen"
    assert scheduler.summary()["jobs_total"] == 0
    assert dequeued is job
    assert collector.merge_results() == "translated"


def test_resume_dashboard_and_regression_are_operational() -> None:
    with TemporaryDirectory() as tmp_dir:
        scheduler = TranslationScheduler()
        jobs = scheduler.create_jobs(["chunk 1"])
        scheduler.queue.mark_running(jobs[0].job_id)
        scheduler.queue.mark_done(jobs[0].job_id, "translated 1")
        scheduler.collector.collect(jobs[0])

        journal = ResumeJournal(Path(tmp_dir) / "freeze_resume.json")
        scheduler.attach_journal(journal)
        journal.save_state(scheduler)
        restored = journal.restore_scheduler()
        report = PerformanceDashboard().build_report(restored, journal)
        checker = PerformanceRegressionChecker()
        baseline = checker.create_snapshot(report, stage="TE-v3.1.6")
        current = checker.create_snapshot(report, stage="TE-v3.1-freeze")
        comparison = checker.compare(baseline, current)

        assert journal.load_state()["schema_version"]
        assert restored.collector.merge_results() == "translated 1"
        assert report["journal"]["restore_ready"] is True
        assert comparison["status"] == "PASS"


def test_manifest_and_freeze_guarantees() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["release_id"] == "TE-v3.1-scheduler-layer-freeze"
    assert manifest["release_id"] == SCHEDULER_LAYER_RELEASE_ID
    assert manifest["status"] == "frozen"
    assert manifest["layer"] == "translation_scheduler"
    assert "performance_regression" in manifest["components"]
    assert "no_provider_runtime_dependency" in manifest["guarantees"]
    assert "TE-v3.2 Runtime Scheduler Adapter" == manifest["next_stage"]


def test_no_provider_http_api_key_or_launcher_dependency() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    before = LAUNCHER_PATH.read_text(encoding="utf-8") if LAUNCHER_PATH.exists() else ""
    try:
        scheduler = TranslationScheduler()
        scheduler.create_jobs(["api-key-free chunk"])
        importlib.import_module("core.translation_scheduler")
        after = LAUNCHER_PATH.read_text(encoding="utf-8") if LAUNCHER_PATH.exists() else ""

        assert scheduler.summary()["jobs_total"] == 1
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert "core.translation_engine.provider_runtime" not in sys.modules
        assert "requests" not in sys.modules
        assert "httpx" not in sys.modules
        assert before == after
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_scheduler_layer_imports_and_components()
    test_resume_dashboard_and_regression_are_operational()
    test_manifest_and_freeze_guarantees()
    test_no_provider_http_api_key_or_launcher_dependency()
    print("NTPE TE-v3.1 Scheduler Layer Freeze PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
