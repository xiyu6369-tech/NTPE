from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSchedulerAdapter, TranslationScheduler


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_existing_scheduler_injection_success_and_failure_without_provider() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    try:
        adapter = RuntimeSchedulerAdapter()
        success_scheduler = TranslationScheduler()
        failure_scheduler = TranslationScheduler()

        success = adapter.run_with_scheduler(
            [{"text": "A", "metadata": {"profile": "mock"}}, {"text": "B"}],
            success_scheduler,
            lambda job: {"text": f"dry {job.source_text}", "metadata": {"attempts": job.attempts}},
            metadata={"stage": "3.2.3"},
        )

        def failure_handler(job):
            if job.chunk_index == 2:
                raise RuntimeError("schema error")
            return f"dry {job.source_text}"

        failure = adapter.run_with_scheduler(["A", "B"], failure_scheduler, failure_handler)

        assert success["scheduler_summary"]["jobs_total"] == 2
        assert success["scheduler_summary"]["done"] == 2
        assert success["merge_ready"] is True
        assert success["export_outputs"]["merged_text"] == "dry A\ndry B"
        assert success_scheduler.queue.all_jobs()[0].metadata["profile"] == "mock"

        assert failure["scheduler_summary"]["jobs_total"] == 2
        assert failure["scheduler_summary"]["done"] == 1
        assert failure["scheduler_summary"]["failed"] == 1
        assert failure["merge_ready"] is False
        assert failure["failed_chunk_report"][0]["chunk_index"] == 2
        assert failure["export_outputs"]["failed_chunks"][0]["error"] == "schema error"

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert "core.translation_engine.provider_runtime" not in sys.modules
        assert "core.production_runtime" not in sys.modules
        assert "requests" not in sys.modules
        assert "httpx" not in sys.modules
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key
