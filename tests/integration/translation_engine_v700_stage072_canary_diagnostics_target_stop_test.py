from __future__ import annotations

import os

import pytest

from core.adaptive_context_canary.model import CanaryRecord
from core.adaptive_context_canary.registry import append_canary_record, clear_canary_records
from core.adaptive_context_canary_validation import (
    CanaryTargetComplete,
    build_canary_production_report,
    canary_validation_session,
)
from core.adaptive_context_runtime_shadow.hook import (
    install_txt_runtime_shadow_hook,
    uninstall_txt_runtime_shadow_hook,
)


def _record(*, activated: bool, reasons: tuple[str, ...] = ()) -> CanaryRecord:
    return CanaryRecord(
        version="7.0.0-stage05",
        package_id="TXT_fixture_000002",
        chunk_index=2,
        target_chunk=2,
        attempted=True,
        activated=activated,
        fallback_used=not activated,
        fallback_reasons=reasons,
        payload_hash_before="a",
        payload_hash_after="b" if activated else "a",
        baseline_context_tokens=100,
        canary_context_tokens=60 if activated else 100,
        estimated_tokens_saved=40 if activated else 0,
        latency_ms=0.25,
        provider_calls_added=0,
        metadata={"content_redacted": True},
    )


def test_report_exposes_exact_fallback_reasons() -> None:
    clear_canary_records()
    append_canary_record(_record(activated=False, reasons=("no-safe-compressed-context",)))
    report = build_canary_production_report(
        {"status": "failed", "records": []},
        target_chunk=2,
        provider_execution_requested=True,
        stage="fixture",
    )
    assert report.fallback_reasons == ("no-safe-compressed-context",)
    assert "canary-fallback:no-safe-compressed-context" in report.limitations
    assert report.status == "pass_without_canary_activation"


def test_controlled_target_stop_marks_success_without_next_provider_call(monkeypatch: pytest.MonkeyPatch) -> None:
    import lts.txt_translation_runtime as runtime

    uninstall_txt_runtime_shadow_hook()

    def fake_builder(*args, **kwargs):
        chunk_index = int(kwargs.get("chunk_index", 0))
        return {
            "package_id": f"TXT_fixture_{chunk_index:06d}",
            "session": {"chunk_index": chunk_index},
            "context": {"previous_chunk_tail": "前一句完整內容。後一句完整內容。"},
            "prompt": {"user_prompt": "前一句完整內容。後一句完整內容。"},
        }

    monkeypatch.setattr(runtime, "build_prompt_package", fake_builder)
    assert install_txt_runtime_shadow_hook() is True
    try:
        with canary_validation_session(target_chunk=2, context_tokens=6):
            runtime.build_prompt_package(chunk_index=2)
            with pytest.raises(CanaryTargetComplete, match="TE_V7_CANARY_TARGET_COMPLETE"):
                runtime.build_prompt_package(chunk_index=3)
    finally:
        uninstall_txt_runtime_shadow_hook()

    clear_canary_records()
    append_canary_record(_record(activated=True))
    regression = {
        "status": "failed",
        "records": [{"status": "failed", "error": "TE_V7_CANARY_TARGET_COMPLETE:target_chunk=2"}],
    }
    report = build_canary_production_report(
        regression,
        target_chunk=2,
        provider_execution_requested=True,
        stage="fixture",
    )
    assert report.target_chunk_completed is True
    assert report.provider_status == "target_chunk_complete"
    assert report.ready is True
    assert report.status == "pass"
    assert report.provider_calls_added == 0
