from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RUNTIME_SCHEDULER_ADAPTER_RELEASE_ID,
    RUNTIME_SCHEDULER_ADAPTER_STAGES,
    RUNTIME_SCHEDULER_ADAPTER_STATUS,
    RuntimeSchedulerAdapter,
    RuntimeSchedulerResumeContract,
    RuntimeSchedulerStateBridge,
    TranslationScheduler,
)
from core.translation_scheduler.runtime_adapter_dry_run import RuntimeAdapterDryRun


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "manifests" / "te_v32_runtime_scheduler_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_v32_runtime_scheduler_freeze_manifest_and_safe_flow() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        adapter = RuntimeSchedulerAdapter()
        dry_run = RuntimeAdapterDryRun(adapter)
        bridge = RuntimeSchedulerStateBridge()
        contract = RuntimeSchedulerResumeContract()

        dry_result = dry_run.run(
            [{"chunk_index": 1, "text": "one"}, {"chunk_index": 2, "text": "two"}],
            handler=lambda chunk: {"text": f"dry {chunk['text']}"},
        )
        bundle = adapter.run_with_scheduler(["one", "two"], TranslationScheduler(), lambda job: f"run {job.chunk_index}")
        runtime_snapshot = bridge.build_runtime_snapshot({**bundle, "runtime_id": "integration-freeze-runtime"})
        resume_plan = contract.build_resume_plan(runtime_snapshot)

        assert RUNTIME_SCHEDULER_ADAPTER_STATUS == "frozen"
        assert RUNTIME_SCHEDULER_ADAPTER_STAGES == ("3.2.1", "3.2.2", "3.2.3", "3.2.4", "3.2.5")
        assert manifest["release_id"] == RUNTIME_SCHEDULER_ADAPTER_RELEASE_ID
        assert manifest["frozen"] is True
        assert manifest["layer"] == "runtime_scheduler_adapter"
        assert len(manifest["validation_commands"]) >= 8
        assert dry_result.merge_ready is True
        assert runtime_snapshot["merge_ready"] is True
        assert resume_plan["reason"] == "already_complete"
        assert contract.validate_resume_plan(resume_plan)["valid"] is True

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key
