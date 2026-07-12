from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _package(index: int, text: str) -> dict[str, object]:
    return {
        "package_id": f"p{index}",
        "session": {"chunk_index": index},
        "context": {"previous_chunk_tail": text},
        "prompt": {"user_prompt": f"CTX\n{text}\nSRC"},
    }


def test_canary_validation_single_activation_and_redacted_report() -> None:
    from core.adaptive_context_canary import apply_prompt_package_canary, clear_canary_records
    from core.adaptive_context_canary_validation import build_canary_production_report, canary_validation_session

    text = ("完整句一。完整句二。完整句三。" * 30)
    clear_canary_records()
    with tempfile.TemporaryDirectory(dir=ROOT) as td:
        audit = Path(td) / "a.jsonl"
        with canary_validation_session(target_chunk=2, context_tokens=20, audit_path=str(audit)):
            r1 = apply_prompt_package_canary(_package(1, text))
            r2 = apply_prompt_package_canary(_package(2, text))
            r3 = apply_prompt_package_canary(_package(3, text))
            assert r1 and not r1.attempted
            assert r2 and r2.activated
            assert r3 and not r3.attempted
            report = build_canary_production_report(
                {"status": "success"}, target_chunk=2, provider_execution_requested=True, stage="x"
            )
            data = report.to_dict()
            assert report.ready and report.activated_records == 1
            assert data["metadata"]["content_redacted"] is True
            assert text not in str(data)
            assert report.provider_calls_added == 0
        assert audit.exists()


def test_provider_timeout_is_limitation_not_ace_blocker() -> None:
    from core.adaptive_context_canary import apply_prompt_package_canary, clear_canary_records
    from core.adaptive_context_canary_validation import build_canary_production_report, canary_validation_session

    text = ("完整句一。完整句二。完整句三。" * 30)
    clear_canary_records()
    with canary_validation_session(target_chunk=2, context_tokens=20):
        apply_prompt_package_canary(_package(2, text))
        report = build_canary_production_report(
            {"status": "failed"}, target_chunk=2, provider_execution_requested=True, stage="x"
        )
        assert report.status == "pass_with_external_provider_limitation"
        assert not report.ready
        assert not report.blockers
        assert "provider-regression-status:failed" in report.limitations


def test_session_restores_exact_environment() -> None:
    from core.adaptive_context_canary_validation import canary_validation_session

    keys = (
        "NTPE_TE_V7_ACE_MODE",
        "NTPE_TE_V7_ACE_CANARY_CHUNK",
        "NTPE_TE_V7_ACE_CANARY_CONTEXT_TOKENS",
        "NTPE_TE_V7_ACE_CANARY_AUDIT",
    )
    previous = {key: os.environ.get(key) for key in keys}
    os.environ["NTPE_TE_V7_ACE_MODE"] = "canary"
    os.environ["NTPE_TE_V7_ACE_CANARY_CHUNK"] = "77"
    before = {key: os.environ.get(key) for key in keys}
    try:
        with canary_validation_session(target_chunk=4, context_tokens=99):
            assert os.environ["NTPE_TE_V7_ACE_MODE"] == "canary"
            assert os.environ["NTPE_TE_V7_ACE_CANARY_CHUNK"] == "4"
        for key, value in before.items():
            assert os.environ.get(key) == value
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_dry_run_without_previous_translation_is_safe_not_failed() -> None:
    from core.adaptive_context_canary import apply_prompt_package_canary, clear_canary_records
    from core.adaptive_context_canary_validation import build_canary_production_report, canary_validation_session

    clear_canary_records()
    with canary_validation_session(target_chunk=2, context_tokens=20):
        apply_prompt_package_canary(_package(2, ""))
        report = build_canary_production_report(
            {"status": "success"}, target_chunk=2, provider_execution_requested=False, stage="dry"
        )
        assert report.status == "pass_without_provider_activation"
        assert not report.ready and not report.blockers
        assert "canary-not-activated" in report.limitations
