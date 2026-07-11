from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RUNTIME_SCHEDULER_ADAPTER_RELEASE_ID,
    RUNTIME_SCHEDULER_ADAPTER_STAGES,
    RUNTIME_SCHEDULER_ADAPTER_STATUS,
    RUNTIME_SCHEDULER_ADAPTER_VERSION,
    RuntimeSchedulerAdapter,
    RuntimeSchedulerResumeContract,
    RuntimeSchedulerStateBridge,
    TranslationScheduler,
)
from core.translation_scheduler.runtime_adapter_dry_run import RuntimeAdapterDryRun


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v32_runtime_scheduler_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_runtime_scheduler_freeze_imports_and_metadata() -> None:
    module = importlib.import_module("core.translation_scheduler")

    assert RuntimeSchedulerAdapter is not None
    assert RuntimeAdapterDryRun is not None
    assert RuntimeSchedulerStateBridge is not None
    assert RuntimeSchedulerResumeContract is not None
    assert module.RUNTIME_SCHEDULER_ADAPTER_VERSION == "TE-v3.2"
    assert RUNTIME_SCHEDULER_ADAPTER_VERSION == "TE-v3.2"
    assert RUNTIME_SCHEDULER_ADAPTER_RELEASE_ID == "TE-v3.2-runtime-scheduler-freeze"
    assert RUNTIME_SCHEDULER_ADAPTER_STATUS == "frozen"
    assert RUNTIME_SCHEDULER_ADAPTER_STAGES == ("3.2.1", "3.2.2", "3.2.3", "3.2.4", "3.2.5")


def test_runtime_scheduler_freeze_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["version"] == "TE-v3.2"
    assert manifest["release_id"] == RUNTIME_SCHEDULER_ADAPTER_RELEASE_ID
    assert manifest["layer"] == "runtime_scheduler_adapter"
    assert manifest["frozen"] is True
    assert [stage["stage"] for stage in manifest["stages"]] == ["3.2.1", "3.2.2", "3.2.3", "3.2.4", "3.2.5"]
    assert "no_provider_runtime_dependency" in manifest["guarantees"]
    assert "no_http_client_calls" in manifest["guarantees"]
    assert "no_api_key_read_write" in manifest["guarantees"]
    assert "launcher_translate_flow_unchanged" in manifest["guarantees"]
    assert "python ntpe_validate.py" in manifest["validation_commands"]
    assert manifest["next_stage"] == "TE-v3.3 Runtime Integration Planning"


def test_runtime_scheduler_freeze_safe_mock_flow() -> None:
    adapter = RuntimeSchedulerAdapter()
    dry_run = RuntimeAdapterDryRun(adapter)
    bridge = RuntimeSchedulerStateBridge()
    contract = RuntimeSchedulerResumeContract()

    dry_result = dry_run.run(
        [{"chunk_index": 1, "text": "A"}, {"chunk_index": 2, "text": "B"}],
        handler=lambda chunk: {"text": f"freeze {chunk['chunk_index']}"},
    )
    scheduler = TranslationScheduler()
    bundle = adapter.run_with_scheduler(["A", "B"], scheduler, lambda job: f"injected {job.chunk_index}")
    snapshot = bridge.build_runtime_snapshot({**bundle, "runtime_id": "freeze-runtime"})
    resume_plan = contract.build_resume_plan(snapshot)

    assert dry_result.merge_ready is True
    assert bundle["merge_ready"] is True
    assert snapshot["runtime_id"] == "freeze-runtime"
    assert resume_plan["reason"] == "already_complete"
    assert contract.validate_resume_plan(resume_plan)["valid"] is True


def test_runtime_scheduler_freeze_no_provider_http_api_key_or_launcher_dependency() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        test_runtime_scheduler_freeze_safe_mock_flow()

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("core.production_runtime" in sys.modules) == before_production_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_runtime_scheduler_freeze_imports_and_metadata()
    test_runtime_scheduler_freeze_manifest()
    test_runtime_scheduler_freeze_safe_mock_flow()
    test_runtime_scheduler_freeze_no_provider_http_api_key_or_launcher_dependency()
    print("NTPE TE-v3.2 Runtime Scheduler Freeze PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
