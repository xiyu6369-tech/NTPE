from __future__ import annotations

import json
import shutil
import socket
import uuid
from dataclasses import replace
from pathlib import Path

import pytest

from core.adaptive_context_provider_execution_freeze import (
    FREEZE_VERSION,
    FakeTransportFreezeContract,
    run_fake_transport_freeze,
    validate_fake_transport_chain,
    verify_freeze_artifact,
    write_freeze_artifact,
)

ROOT = Path(__file__).resolve().parents[2]


def _contract(**changes: object) -> FakeTransportFreezeContract:
    values: dict[str, object] = {
        "enabled": True,
        "authorization_id": "stage108-authorization",
        "session_id": "stage108-session",
        "source_fingerprint": "a" * 64,
        "chunk_fingerprint": "b" * 64,
        "single_chunk_only": True,
        "single_controlled_session": True,
    }
    values.update(changes)
    return FakeTransportFreezeContract(**values)


def _run(outcomes: tuple[str, ...] = ("success",), *, output_tokens: int = 80):
    return run_fake_transport_freeze(
        _contract(), root=ROOT, outcomes=outcomes, estimated_output_tokens=output_tokens,
    )


def test_freeze_is_disabled_by_default() -> None:
    blockers = FakeTransportFreezeContract().validate()
    assert "provider-execution-freeze-explicit-opt-in-required" in blockers


@pytest.mark.parametrize("field,value,blocker", [
    ("authorization_id", "", "authorization-id-required"),
    ("session_id", "", "session-id-required"),
    ("source_fingerprint", "raw", "source-fingerprint-invalid"),
    ("chunk_fingerprint", "raw", "chunk-fingerprint-invalid"),
    ("single_chunk_only", False, "single-chunk-required"),
    ("single_controlled_session", False, "single-session-required"),
])
def test_freeze_contract_fails_closed(field: str, value: object, blocker: str) -> None:
    assert blocker in ",".join(_contract(**{field: value}).validate())


def test_fake_transport_full_chain_freezes() -> None:
    result = _run()
    assert result.artifact.status == "fake_transport_end_to_end_frozen"
    assert result.evidence.status == "evidence_complete_mock_only"
    assert result.cli_result.harness_result.invocation.session.summary.state == "completed"


def test_explicit_authorization_contract_is_confirmed_without_persisting_value() -> None:
    result = _run()
    assert result.cli_result.harness_result.authorization_confirmed is True
    assert "stage108-authorization" not in json.dumps(result.artifact.__dict__)


def test_single_chunk_and_single_session_are_frozen() -> None:
    harness = _run().cli_result.harness_result
    assert harness.single_chunk_only is True
    assert harness.single_controlled_session is True
    assert harness.invocation.session.summary.attempts_executed == 1


def test_retry_has_independent_timing_evidence() -> None:
    rows = _run(("timeout", "success")).evidence.attempts
    assert len(rows) == 2
    assert [row.retry_count for row in rows] == [0, 1]
    assert all(row.timing_complete for row in rows)


def test_timeout_is_classified_as_external_failure() -> None:
    row = _run(("timeout",)).evidence.attempts[0]
    assert row.timeout is True and row.external_condition_failure is True
    assert row.attempt_status == "failed"


def test_http_503_is_classified_separately() -> None:
    row = _run(("503",)).evidence.attempts[0]
    assert row.http_503 is True and row.timeout is False
    assert row.external_condition_failure is True


def test_exception_like_failure_is_redacted() -> None:
    result = _run(("failure",))
    serialized = json.dumps(result.evidence.to_dict(), sort_keys=True)
    assert result.evidence.attempts[0].external_condition_failure is True
    assert "exception body secret" not in serialized
    assert "response_body" not in serialized and "api_key" not in serialized


def test_fallback_provenance_is_preserved() -> None:
    rows = _run(("timeout", "success")).evidence.attempts
    assert rows[0].fallback_used is False
    assert rows[1].fallback_used is True


def test_payload_and_prompt_are_not_modified() -> None:
    result = _run()
    assert result.artifact.payload_preserved is True
    assert result.artifact.prompt_preserved is True


def test_short_output_is_flagged_and_never_ready() -> None:
    result = _run(output_tokens=1)
    assert result.evidence.short_output_suspicion is True
    assert result.evidence.ready_for_benchmark is False
    assert result.artifact.provider_benchmark_complete is False


def test_resume_exclusion_is_accepted_only_as_excluded_mock_evidence() -> None:
    result = _run()
    evidence = replace(
        result.evidence,
        attempts=(),
        status="excluded_resume",
        evidence_complete=False,
        resume_excluded=True,
        limitations=("resume-chunk-excluded",),
    )
    assert validate_fake_transport_chain(result.cli_result, evidence) == ()


def test_real_provenance_claim_fails_closed() -> None:
    result = _run()
    evidence = replace(result.evidence, evidence_provenance="real")
    blockers = validate_fake_transport_chain(result.cli_result, evidence)
    assert "provider-execution-freeze-real-provenance-forbidden" in blockers


def test_network_request_count_is_zero() -> None:
    result = _run()
    assert result.artifact.network_requests == 0
    assert result.cli_result.network_requests == 0


def test_socket_network_access_is_never_used(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access forbidden")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    assert _run().artifact.network_requests == 0


def test_real_provider_is_never_executed() -> None:
    result = _run()
    assert result.artifact.real_provider_executed is False
    assert result.cli_result.harness_result.real_provider_execution is False
    assert result.cli_result.harness_result.invocation.real_provider_execution is False


def test_no_comparison_or_readiness_is_evaluated() -> None:
    artifact = _run().artifact
    assert artifact.comparison_executed is False
    assert artifact.readiness_evaluated is False
    assert artifact.provider_benchmark_complete is False


def test_stage09_artifacts_remain_unchanged() -> None:
    assert _run().artifact.stage09_artifacts_unchanged is True


def test_te_v6_frozen_runtime_remains_unchanged() -> None:
    assert _run().artifact.te_v6_frozen_runtime_unchanged is True


def test_no_production_launcher_is_connected() -> None:
    result = _run()
    assert result.artifact.production_launcher_connected is False
    source = (ROOT / "core/adaptive_context_provider_execution_freeze/freeze.py").read_text(encoding="utf-8")
    assert "import launcher_translate" not in source
    assert "ntpe_production_translate" not in source


def test_freeze_artifact_round_trip_and_integrity() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage108" / uuid.uuid4().hex
    report = sandbox / "freeze.json"
    try:
        write_freeze_artifact(_run().artifact, report, root=ROOT)
        verified = verify_freeze_artifact(report)
        assert verified.status == "fake_transport_end_to_end_frozen"
        assert verified.network_requests == 0
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage108", ignore_errors=True)


def test_freeze_artifact_tampering_fails_closed() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage108_tamper" / uuid.uuid4().hex
    report = sandbox / "freeze.json"
    try:
        write_freeze_artifact(_run().artifact, report, root=ROOT)
        payload = json.loads(report.read_text(encoding="utf-8"))
        payload["network_requests"] = 1
        report.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError, match="integrity failure"):
            verify_freeze_artifact(report)
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage108_tamper", ignore_errors=True)


def test_freeze_artifact_path_is_protected() -> None:
    with pytest.raises(ValueError, match="path-forbidden"):
        write_freeze_artifact(_run().artifact, ROOT / "outside108.json", root=ROOT)


def test_stage09_overwrite_path_is_protected() -> None:
    with pytest.raises(ValueError):
        write_freeze_artifact(
            _run().artifact, ROOT / "artifacts/te_v7_stage09/freeze.json", root=ROOT,
        )


def test_freeze_version_and_non_benchmark_claims_are_explicit() -> None:
    artifact = _run().artifact
    assert FREEZE_VERSION == "7.0.0-stage10.8"
    assert artifact.version == FREEZE_VERSION
    assert not hasattr(artifact, "latency_improved")
    assert not hasattr(artifact, "translation_quality_improved")
