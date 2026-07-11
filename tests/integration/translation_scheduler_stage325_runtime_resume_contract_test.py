from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RuntimeSchedulerAdapter,
    RuntimeSchedulerResumeContract,
    RuntimeSchedulerStateBridge,
    TranslationScheduler,
)


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_resume_contract_with_bridge_and_scheduler_bundle_without_provider() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        bridge = RuntimeSchedulerStateBridge()
        contract = RuntimeSchedulerResumeContract()

        partial_snapshot = bridge.build_scheduler_snapshot(
            {
                "runtime_id": "integration-partial-325",
                "chunks": [
                    {"chunk_index": 1, "status": "done"},
                    {"chunk_index": 2, "status": "pending"},
                    {"chunk_index": 3, "status": "failed"},
                ],
            }
        )
        partial_plan = contract.build_resume_plan(partial_snapshot)

        adapter = RuntimeSchedulerAdapter()
        scheduler = TranslationScheduler()

        def handler(job):
            if job.chunk_index == 2:
                raise RuntimeError("schema error")
            return f"ok {job.chunk_index}"

        bundle = adapter.run_with_scheduler(["one", "two"], scheduler, handler)
        runtime_snapshot = bridge.build_runtime_snapshot({**bundle, "runtime_id": "integration-runtime-325"})
        runtime_plan = contract.build_resume_plan(runtime_snapshot)

        complete_plan = contract.build_resume_plan(
            bridge.build_scheduler_snapshot(
                {
                    "runtime_id": "integration-complete-325",
                    "chunks": [{"chunk_index": 1, "status": "success"}],
                }
            )
        )

        assert partial_plan["runtime_id"] == "integration-partial-325"
        assert partial_plan["resume_chunks"] == [2, 3]
        assert partial_plan["skip_chunks"] == [1]
        assert partial_plan["failed_chunks"] == [3]
        assert partial_plan["resumable"] is True
        assert partial_plan["reason"] == "resume_required"
        assert contract.validate_resume_plan(partial_plan)["valid"] is True

        assert runtime_plan["runtime_id"] == "integration-runtime-325"
        assert runtime_plan["chunks_total"] == 2
        assert runtime_plan["resume_chunks"] == [2]
        assert runtime_plan["skip_chunks"] == [1]
        assert runtime_plan["failed_chunks"] == [2]
        assert runtime_plan["resumable"] is True
        assert contract.validate_resume_plan(runtime_plan)["valid"] is True

        assert complete_plan["resumable"] is False
        assert complete_plan["reason"] == "already_complete"
        assert contract.validate_resume_plan(contract.build_resume_plan({}))["valid"] is True

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key
