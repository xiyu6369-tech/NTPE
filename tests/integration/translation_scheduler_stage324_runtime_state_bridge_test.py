from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSchedulerAdapter, RuntimeSchedulerStateBridge, TranslationScheduler


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_runtime_scheduler_state_bridge_round_trip_shapes_without_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        bridge = RuntimeSchedulerStateBridge()
        scheduler_snapshot = bridge.build_scheduler_snapshot(
            {
                "runtime_id": "integration-runtime-324",
                "session": {
                    "chunks": [
                        {"index": 1, "status": "success"},
                        {"index": 2, "status": "queued"},
                        {"index": 3, "status": "error"},
                    ]
                },
                "metadata": {"source": "integration"},
            }
        )

        adapter = RuntimeSchedulerAdapter()
        scheduler = TranslationScheduler()
        bundle = adapter.run_with_scheduler(
            ["one", "two"],
            scheduler,
            lambda job: {"text": f"ok {job.chunk_index}", "metadata": {"mock": True}},
        )
        runtime_snapshot = bridge.build_runtime_snapshot({**bundle, "runtime_id": "integration-bundle-324"})
        empty_runtime_snapshot = bridge.build_runtime_snapshot({})

        assert scheduler_snapshot["chunks_total"] == 3
        assert scheduler_snapshot["pending_chunks"] == [2]
        assert scheduler_snapshot["done_chunks"] == [1]
        assert scheduler_snapshot["failed_chunks"] == [3]
        assert scheduler_snapshot["merge_ready"] is False
        assert scheduler_snapshot["metadata"]["source"] == "integration"
        assert bridge.validate_snapshot(scheduler_snapshot)["valid"] is True

        assert runtime_snapshot["runtime_id"] == "integration-bundle-324"
        assert runtime_snapshot["scheduler_summary"]["done"] == 2
        assert runtime_snapshot["collector_manifest"]["done_chunks"] == [1, 2]
        assert runtime_snapshot["outputs_count"] == 2
        assert runtime_snapshot["merge_ready"] is True
        assert runtime_snapshot["failed_chunk_report"] == []
        assert bridge.validate_snapshot(runtime_snapshot)["valid"] is True

        assert empty_runtime_snapshot["runtime_id"] == "runtime-state-unknown"
        assert empty_runtime_snapshot["outputs_count"] == 0
        assert empty_runtime_snapshot["merge_ready"] is False
        assert bridge.validate_snapshot(empty_runtime_snapshot)["valid"] is True

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key
