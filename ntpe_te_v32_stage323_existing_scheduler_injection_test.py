from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSchedulerAdapter, TranslationScheduler


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_existing_scheduler_success_flow() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    try:
        adapter = RuntimeSchedulerAdapter()
        scheduler = TranslationScheduler()
        injected_id = id(scheduler)

        result = adapter.run_with_scheduler(
            ["chunk 1", "chunk 2"],
            scheduler,
            lambda job: {"text": f"injected translated {job.chunk_index}", "metadata": {"dry_run": True}},
            metadata={"stage": "3.2.3", "runtime_source": "existing-scheduler"},
        )

        assert id(scheduler) == injected_id
        assert result["scheduler_summary"]["jobs_total"] == 2
        assert result["scheduler_summary"]["done"] == 2
        assert result["scheduler_summary"]["failed"] == 0
        assert result["outputs_count"] == 2
        assert result["merge_ready"] is True
        assert result["collector_manifest"]["done_chunks"] == [1, 2]
        assert result["failed_chunk_report"] == []
        assert result["export_outputs"]["merged_text"] == "injected translated 1\ninjected translated 2"
        assert result["export_outputs"]["chunk_results"][0]["metadata"] == {"dry_run": True}
        assert scheduler.queue.all_jobs()[0].metadata["stage"] == "3.2.3"
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert "core.translation_engine.provider_runtime" not in sys.modules
        assert "core.production_runtime" not in sys.modules
        assert "requests" not in sys.modules
        assert "httpx" not in sys.modules
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def test_existing_scheduler_failure_blocks_merge_ready() -> None:
    adapter = RuntimeSchedulerAdapter()
    scheduler = TranslationScheduler()

    def handler(job):
        if job.chunk_index == 2:
            raise RuntimeError("schema error")
        return f"injected translated {job.chunk_index}"

    result = adapter.run_with_scheduler(["chunk 1", "chunk 2"], scheduler, handler)

    assert result["scheduler_summary"]["done"] == 1
    assert result["scheduler_summary"]["failed"] == 1
    assert result["merge_ready"] is False
    assert result["failed_chunk_report"][0]["chunk_index"] == 2
    assert result["export_outputs"]["failed_chunks"][0]["error"] == "schema error"
    assert result["export_outputs"]["merged_text"] == "injected translated 1"


def main() -> int:
    test_existing_scheduler_success_flow()
    test_existing_scheduler_failure_blocks_merge_ready()
    print("NTPE TE-v3.2 Stage-3.2.3 Existing Scheduler Injection PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
