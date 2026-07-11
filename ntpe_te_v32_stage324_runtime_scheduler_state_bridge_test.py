from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSchedulerAdapter, RuntimeSchedulerStateBridge, TranslationScheduler


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_runtime_state_to_scheduler_snapshot_success_and_defaults() -> None:
    bridge = RuntimeSchedulerStateBridge()

    success = bridge.build_scheduler_snapshot(
        {
            "runtime_id": "runtime-324",
            "chunks": [
                {"chunk_index": 1, "status": "done"},
                {"chunk_index": 2, "status": "completed"},
            ],
            "metadata": {"profile": "mock"},
        }
    )
    defaults = bridge.build_scheduler_snapshot({})

    assert success["runtime_id"] == "runtime-324"
    assert success["chunks_total"] == 2
    assert success["pending_chunks"] == []
    assert success["done_chunks"] == [1, 2]
    assert success["failed_chunks"] == []
    assert success["merge_ready"] is True
    assert success["metadata"]["profile"] == "mock"
    assert bridge.validate_snapshot(success)["valid"] is True

    assert defaults["runtime_id"] == "runtime-state-unknown"
    assert defaults["chunks_total"] == 0
    assert defaults["merge_ready"] is False
    assert bridge.validate_snapshot(defaults)["valid"] is True


def test_failed_runtime_state_and_scheduler_bundle_to_runtime_snapshot_without_provider() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    try:
        bridge = RuntimeSchedulerStateBridge()
        failed_scheduler_snapshot = bridge.build_scheduler_snapshot(
            {
                "session_id": "session-324",
                "jobs": [
                    {"chunk_index": 1, "status": "done"},
                    {"chunk_index": 2, "status": "failed"},
                ],
            }
        )

        adapter = RuntimeSchedulerAdapter()
        scheduler = TranslationScheduler()

        def handler(job):
            if job.chunk_index == 2:
                raise RuntimeError("schema error")
            return f"translated {job.chunk_index}"

        bundle = adapter.run_with_scheduler(["chunk 1", "chunk 2"], scheduler, handler)
        runtime_snapshot = bridge.build_runtime_snapshot({**bundle, "runtime_id": "runtime-bundle-324"})

        assert failed_scheduler_snapshot["runtime_id"] == "session-324"
        assert failed_scheduler_snapshot["done_chunks"] == [1]
        assert failed_scheduler_snapshot["failed_chunks"] == [2]
        assert failed_scheduler_snapshot["merge_ready"] is False
        assert bridge.validate_snapshot(failed_scheduler_snapshot)["valid"] is True

        assert runtime_snapshot["runtime_id"] == "runtime-bundle-324"
        assert runtime_snapshot["scheduler_summary"]["jobs_total"] == 2
        assert runtime_snapshot["collector_manifest"]["failed_chunks"] == [2]
        assert runtime_snapshot["outputs_count"] == 1
        assert runtime_snapshot["merge_ready"] is False
        assert runtime_snapshot["failed_chunk_report"][0]["chunk_index"] == 2
        assert runtime_snapshot["metadata"]["stage"] == "3.2.4"
        assert bridge.validate_snapshot(runtime_snapshot)["valid"] is True

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert "core.translation_engine.provider_runtime" not in sys.modules
        assert "core.production_runtime" not in sys.modules
        assert "requests" not in sys.modules
        assert "httpx" not in sys.modules
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_runtime_state_to_scheduler_snapshot_success_and_defaults()
    test_failed_runtime_state_and_scheduler_bundle_to_runtime_snapshot_without_provider()
    print("NTPE TE-v3.2 Stage-3.2.4 Runtime Scheduler State Bridge PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
