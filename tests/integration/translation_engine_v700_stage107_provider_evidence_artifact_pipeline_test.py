from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import replace
from pathlib import Path

import pytest

from core.adaptive_context_authorized_provider_cli import (
    AuthorizedProviderCliConfig,
    run_authorized_provider_cli,
)
from core.adaptive_context_authorized_provider_harness import FakeAuthorizedProviderTransport
from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.adaptive_context_provider_evidence_pipeline import (
    EVIDENCE_STATUSES,
    PIPELINE_VERSION,
    ProviderEvidencePipelineConfig,
    collect_provider_evidence_artifact,
    validate_provider_evidence_artifact,
    verify_provider_evidence_artifact,
    write_provider_evidence_artifact,
)

ROOT = Path(__file__).resolve().parents[2]
MODEL = "meta/llama-3.3-70b-instruct"


def _harness_result(
    outcomes: tuple[str, ...] = ("success",), *, output_tokens: int = 80,
):
    config = AuthorizedProviderCliConfig(
        boundary_enabled=True,
        real_provider_enabled=True,
        authorization_id="stage107-authorization",
        execution_mode="fake",
        session_id="stage107-session",
        source_fingerprint="a" * 64,
        chunk_fingerprint="b" * 64,
    )
    plans = tuple(
        ProviderAttemptPlan(index, MODEL, 30 if index == 1 else 60, index > 1, 100, output_tokens)
        for index in range(1, len(outcomes) + 1)
    )
    return run_authorized_provider_cli(
        config, root=ROOT, transport=FakeAuthorizedProviderTransport(outcomes),
        plans=plans, environ={},
    ).harness_result


def _collect(outcomes: tuple[str, ...] = ("success",), *, output_tokens: int = 80):
    return collect_provider_evidence_artifact(
        _harness_result(outcomes, output_tokens=output_tokens),
        ProviderEvidencePipelineConfig(enabled=True, declared_provenance="mock"),
    )


def test_pipeline_is_disabled_by_default() -> None:
    assert "explicit-opt-in-required" in ",".join(ProviderEvidencePipelineConfig().validate())


@pytest.mark.parametrize("field,value,blocker", [
    ("declared_provenance", "fake", "provenance-invalid"),
    ("single_chunk_only", False, "single-chunk-required"),
    ("preserve_payload_required", False, "payload-preservation-required"),
    ("preserve_prompt_required", False, "prompt-preservation-required"),
])
def test_pipeline_configuration_fails_closed(field: str, value: object, blocker: str) -> None:
    config = ProviderEvidencePipelineConfig(enabled=True, **{field: value})
    assert blocker in ",".join(config.validate())


def test_fake_transport_normalizes_to_mock_only_evidence() -> None:
    artifact = _collect()
    assert artifact.transport_provenance == "fake"
    assert artifact.evidence_provenance == "mock"
    assert artifact.status == "evidence_complete_mock_only"
    assert artifact.ready_for_benchmark is False


def test_fake_evidence_cannot_be_declared_real() -> None:
    artifact = collect_provider_evidence_artifact(
        _harness_result(),
        ProviderEvidencePipelineConfig(enabled=True, declared_provenance="real"),
    )
    assert artifact.status == "rejected_provenance"
    assert artifact.ready_for_benchmark is False


def test_retry_attempts_remain_independent() -> None:
    artifact = _collect(("timeout", "success"))
    assert [row.attempt_number for row in artifact.attempts] == [1, 2]
    assert [row.retry_count for row in artifact.attempts] == [0, 1]


def test_timeout_is_not_treated_as_latency_improvement() -> None:
    artifact = _collect(("timeout",))
    assert artifact.attempts[0].timeout is True
    assert artifact.attempts[0].attempt_status == "failed"
    assert "provider-run-incomplete" in artifact.limitations


def test_http_503_classification_is_preserved() -> None:
    artifact = _collect(("503",))
    row = artifact.attempts[0]
    assert row.http_503 is True and row.external_condition_failure is True


def test_fallback_evidence_is_preserved() -> None:
    artifact = _collect(("timeout", "success"))
    assert artifact.attempts[0].fallback_used is False
    assert artifact.attempts[1].fallback_used is True


def test_token_and_timing_evidence_are_normalized() -> None:
    row = _collect().attempts[0]
    assert row.estimated_input_tokens == 100
    assert row.estimated_output_tokens == 80
    assert row.timing_complete is True and row.elapsed_milliseconds is not None


def test_short_output_suspicion_prevents_ready_status() -> None:
    artifact = _collect(output_tokens=1)
    assert artifact.short_output_suspicion is True
    assert artifact.ready_for_benchmark is False
    assert "suspicious-short-output" in artifact.limitations


def test_payload_and_prompt_preservation_are_explicit() -> None:
    artifact = _collect()
    assert artifact.payload_preserved is True
    assert artifact.prompt_preserved is True


def test_resume_chunk_is_excluded() -> None:
    result = _harness_result()
    session = result.invocation.session
    evidence = replace(
        session.evidence,
        records=(),
        excluded_resume_chunks=({"chunk_index": 1, "reason": "resume-chunk-excluded"},),
    )
    session = replace(session, evidence=evidence)
    result = replace(result, invocation=replace(result.invocation, session=session))
    artifact = collect_provider_evidence_artifact(
        result, ProviderEvidencePipelineConfig(enabled=True, declared_provenance="mock"),
    )
    assert artifact.status == "excluded_resume"
    assert artifact.resume_excluded is True and not artifact.attempts


def test_status_vocabulary_contains_all_required_states() -> None:
    assert EVIDENCE_STATUSES == {
        "evidence_complete_mock_only", "evidence_complete_provider_limited",
        "ready_for_benchmark", "evidence_incomplete", "excluded_resume",
        "rejected_provenance", "rejected_integrity",
    }


def test_artifact_contains_safe_identity_not_source_content() -> None:
    artifact = _collect()
    serialized = json.dumps(artifact.to_dict(), sort_keys=True)
    assert artifact.source_fingerprint == "a" * 64
    assert artifact.chunk_fingerprint == "b" * 64
    assert "stage107-raw-source-content" not in serialized
    assert "stage107-raw-prompt-content" not in serialized


def test_exception_or_response_content_has_no_artifact_field() -> None:
    serialized = json.dumps(_collect(("failure",)).to_dict(), sort_keys=True)
    assert "exception" not in serialized
    assert "response_body" not in serialized and "request_body" not in serialized
    assert "authorization" not in serialized and "api_key" not in serialized


def test_artifact_writer_and_verifier_preserve_integrity() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage107" / uuid.uuid4().hex
    report = sandbox / "evidence.json"
    try:
        write_provider_evidence_artifact(_collect(), report, root=ROOT)
        verified = verify_provider_evidence_artifact(report)
        assert verified.status == "evidence_complete_mock_only"
        assert len(verified.attempts) == 1
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage107", ignore_errors=True)


def test_integrity_tampering_is_rejected() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage107_tamper" / uuid.uuid4().hex
    report = sandbox / "evidence.json"
    try:
        write_provider_evidence_artifact(_collect(), report, root=ROOT)
        payload = json.loads(report.read_text(encoding="utf-8"))
        payload["model"] = "tampered"
        report.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError, match="rejected_integrity"):
            verify_provider_evidence_artifact(report)
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage107_tamper", ignore_errors=True)


def test_artifact_path_outside_stage10_is_rejected() -> None:
    with pytest.raises(ValueError, match="outside-stage10-sandbox"):
        write_provider_evidence_artifact(_collect(), ROOT / "outside107.json", root=ROOT)


def test_stage09_artifact_path_is_rejected() -> None:
    with pytest.raises(ValueError):
        write_provider_evidence_artifact(
            _collect(), ROOT / "artifacts/te_v7_stage09/evidence.json", root=ROOT,
        )


def test_pipeline_never_evaluates_comparison_quality_or_readiness() -> None:
    artifact = _collect()
    assert artifact.baseline_candidate_compared is False
    assert artifact.production_readiness_evaluated is False
    assert artifact.rollout_readiness_evaluated is False
    assert artifact.translation_quality_evaluated is False


def test_validator_rejects_comparison_claim() -> None:
    blockers = validate_provider_evidence_artifact(
        replace(_collect(), baseline_candidate_compared=True),
    )
    assert "provider-evidence-artifact-comparison-forbidden" in blockers


def test_pipeline_version_is_stage_local() -> None:
    assert PIPELINE_VERSION == "7.0.0-stage10.7"
