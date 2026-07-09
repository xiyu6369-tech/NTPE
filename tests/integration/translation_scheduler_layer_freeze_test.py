from __future__ import annotations

import json
import os
from pathlib import Path

from core.translation_scheduler import PerformanceDashboard, PerformanceRegressionChecker, ResumeJournal, TranslationScheduler


ROOT = Path(__file__).resolve().parents[2]


def test_scheduler_layer_freeze_flow_without_api_key(tmp_path: Path) -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    try:
        scheduler = TranslationScheduler(default_max_attempts=2)
        scheduler.create_jobs(["chunk 1", "chunk 2", "chunk 3"])
        calls: dict[int, int] = {}

        def handler(job):
            calls[job.chunk_index] = calls.get(job.chunk_index, 0) + 1
            if job.chunk_index == 2 and calls[job.chunk_index] == 1:
                raise TimeoutError("provider timeout")
            if job.chunk_index == 3:
                raise RuntimeError("authentication failed")
            return f"translated {job.chunk_index}"

        scheduler.run(handler)
        assert scheduler.collector.merge_results() == "translated 1\ntranslated 2"
        assert scheduler.queue.done_count() == 2
        assert scheduler.queue.failed_count() == 1

        journal = ResumeJournal(tmp_path / "freeze_resume.json")
        scheduler.attach_journal(journal)
        scheduler.save_journal()
        restored = journal.restore_scheduler()
        assert restored.collector.merge_results() == "translated 1\ntranslated 2"

        dashboard = PerformanceDashboard()
        report = dashboard.build_report(restored, journal)
        checker = PerformanceRegressionChecker()
        baseline = checker.create_snapshot(report, stage="TE-v3.1.6", source="freeze-integration")
        current = checker.create_snapshot(report, stage="TE-v3.1-freeze", source="freeze-integration")
        comparison = checker.compare(baseline, current)

        manifest = json.loads((ROOT / "manifests" / "te_v31_scheduler_layer_manifest.json").read_text(encoding="utf-8"))
        assert comparison["status"] == "PASS"
        assert report["journal"]["journal_exists"] is True
        assert manifest["release_id"] == "TE-v3.1-scheduler-layer-freeze"
        assert manifest["status"] == "frozen"
        assert os.environ.get("NVIDIA_API_KEY") is None
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key
