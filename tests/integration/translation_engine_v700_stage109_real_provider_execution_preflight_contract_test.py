from __future__ import annotations

import json
import shutil
import socket
import uuid
from dataclasses import replace
from pathlib import Path

import pytest

import core.adaptive_context_real_provider_preflight.validator as preflight_validator
from core.adaptive_context_real_provider_preflight import (
    MAX_PREFLIGHT_ATTEMPTS,
    PREFLIGHT_STATUSES,
    PREFLIGHT_VERSION,
    PreflightAttemptPlan,
    RealProviderPreflightConfig,
    evaluate_real_provider_preflight,
    resolve_preflight_artifact_path,
    verify_preflight_artifact,
    write_preflight_artifact,
)

ROOT = Path(__file__).resolve().parents[2]
MODEL = "meta/llama-3.3-70b-instruct"
URL = "https://integrate.api.nvidia.com/v1/chat/completions"
FAKE_CREDENTIAL = "stage109-fake-credential-must-never-leak"
AUTHORIZATION = "stage109-authorization-001"


def _config(**changes: object) -> RealProviderPreflightConfig:
    values: dict[str, object] = {
        "enabled": True,
        "boundary_enabled": True,
        "real_provider_enabled": True,
        "authorization_id": AUTHORIZATION,
        "provider": "nvidia",
        "provider_url": URL,
        "model": MODEL,
        "fallback_models": (),
        "attempt_plan": (PreflightAttemptPlan(1, MODEL, 30, False),),
        "max_retries": 1,
        "source_identity": "stage109-source-001",
        "source_fingerprint": "a" * 64,
        "chunk_count": 1,
        "single_chunk_only": True,
        "single_controlled_session": True,
        "resumed": False,
        "artifact_path": "artifacts/te_v7_stage109/TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT.json",
    }
    values.update(changes)
    return RealProviderPreflightConfig(**values)


def _evaluate(config: RealProviderPreflightConfig | None = None, *, environ=None):
    return evaluate_real_provider_preflight(
        config or _config(), root=ROOT,
        environ={"NVIDIA_API_KEY": FAKE_CREDENTIAL} if environ is None else environ,
    )


def test_preflight_is_disabled_by_default() -> None:
    result = _evaluate(RealProviderPreflightConfig(), environ={})
    assert result.artifact.status == "disabled"
    assert result.artifact.eligible is False


def test_missing_boundary_enable_is_blocked() -> None:
    assert _evaluate(_config(boundary_enabled=False)).artifact.status == "blocked_missing_boundary_enable"


def test_missing_real_provider_enable_is_blocked() -> None:
    assert _evaluate(_config(real_provider_enabled=False)).artifact.status == "blocked_missing_real_provider_enable"


def test_missing_authorization_is_blocked() -> None:
    result = _evaluate(_config(authorization_id=""))
    assert result.artifact.status == "blocked_missing_authorization"
    assert result.artifact.authorization_recorded is False


@pytest.mark.parametrize("authorization", ["a", "contains space", "bad/slash", "*unsafe*"])
def test_invalid_authorization_format_is_blocked(authorization: str) -> None:
    result = _evaluate(_config(authorization_id=authorization))
    assert result.artifact.status == "blocked_invalid_authorization"


def test_missing_environment_credential_is_blocked() -> None:
    result = _evaluate(environ={})
    assert result.artifact.status == "blocked_missing_credential"
    assert result.artifact.credential_available is False


def test_empty_environment_credential_is_blocked() -> None:
    assert _evaluate(environ={"NVIDIA_API_KEY": ""}).artifact.status == "blocked_missing_credential"


def test_credential_and_authorization_values_are_not_in_artifact() -> None:
    serialized = json.dumps(_evaluate().artifact.to_dict(), sort_keys=True)
    assert FAKE_CREDENTIAL not in serialized
    assert AUTHORIZATION not in serialized
    assert "credential_length" not in serialized
    assert "credential_fingerprint" not in serialized


def test_invalid_endpoint_is_blocked() -> None:
    assert _evaluate(_config(provider_url="https://invalid.example/v1")).artifact.status == "blocked_invalid_endpoint"


def test_invalid_provider_is_blocked_as_endpoint_contract() -> None:
    assert _evaluate(_config(provider="custom")).artifact.status == "blocked_invalid_endpoint"


def test_invalid_primary_model_is_blocked() -> None:
    assert _evaluate(_config(model="unapproved-model")).artifact.status == "blocked_invalid_model"


def test_invalid_fallback_model_is_blocked() -> None:
    assert _evaluate(_config(fallback_models=("unapproved-fallback",))).artifact.status == "blocked_invalid_model"


def test_empty_attempt_plan_is_blocked() -> None:
    assert _evaluate(_config(attempt_plan=())).artifact.status == "blocked_invalid_attempt_plan"


def test_excessive_attempts_are_blocked() -> None:
    plans = tuple(PreflightAttemptPlan(i, MODEL, 30, i > 1) for i in range(1, 5))
    result = _evaluate(_config(attempt_plan=plans, max_retries=3))
    assert MAX_PREFLIGHT_ATTEMPTS == 3
    assert result.artifact.status == "blocked_invalid_attempt_plan"


def test_retry_count_must_have_explicit_bound() -> None:
    plans = (
        PreflightAttemptPlan(1, MODEL, 30, False),
        PreflightAttemptPlan(2, MODEL, 60, True),
    )
    assert _evaluate(_config(attempt_plan=plans, max_retries=0)).artifact.status == "blocked_invalid_attempt_plan"


@pytest.mark.parametrize("timeout", [0, -1])
def test_timeout_must_be_positive(timeout: int) -> None:
    plan = (PreflightAttemptPlan(1, MODEL, timeout, False),)
    assert _evaluate(_config(attempt_plan=plan)).artifact.status == "blocked_invalid_attempt_plan"


def test_attempt_numbers_must_be_sequential() -> None:
    plan = (PreflightAttemptPlan(2, MODEL, 30, True),)
    assert _evaluate(_config(attempt_plan=plan)).artifact.status == "blocked_invalid_attempt_plan"


def test_fallback_marker_is_required_after_first_attempt() -> None:
    plans = (
        PreflightAttemptPlan(1, MODEL, 30, False),
        PreflightAttemptPlan(2, MODEL, 60, False),
    )
    assert _evaluate(_config(attempt_plan=plans)).artifact.status == "blocked_invalid_attempt_plan"


@pytest.mark.parametrize("changes", [
    {"chunk_count": 2},
    {"single_chunk_only": False},
    {"single_controlled_session": False},
])
def test_multiple_chunk_or_session_contract_is_blocked(changes: dict[str, object]) -> None:
    assert _evaluate(_config(**changes)).artifact.status == "blocked_invalid_attempt_plan"


def test_resume_chunk_is_rejected() -> None:
    result = _evaluate(_config(resumed=True))
    assert result.artifact.status == "blocked_resume_chunk"
    assert result.artifact.resume_excluded is False


def test_invalid_source_identity_is_blocked() -> None:
    assert _evaluate(_config(source_identity="")).artifact.status == "blocked_invalid_source_identity"


@pytest.mark.parametrize("fingerprint", ["", "not-a-hash", "g" * 64])
def test_invalid_source_fingerprint_is_blocked(fingerprint: str) -> None:
    result = _evaluate(_config(source_fingerprint=fingerprint))
    assert result.artifact.status == "blocked_invalid_source_fingerprint"


def test_invalid_artifact_extension_is_blocked() -> None:
    result = _evaluate(_config(artifact_path="artifacts/te_v7_stage109/preflight.txt"))
    assert result.artifact.status == "blocked_artifact_path"


def test_artifact_path_escape_is_blocked() -> None:
    result = _evaluate(_config(artifact_path="outside-stage109.json"))
    assert result.artifact.status == "blocked_artifact_path"


def test_stage09_overwrite_path_is_blocked() -> None:
    result = _evaluate(_config(artifact_path="artifacts/te_v7_stage09/preflight.json"))
    assert result.artifact.status == "blocked_artifact_path"


def test_stage108_artifact_path_must_be_canonical() -> None:
    result = _evaluate(_config(stage108_freeze_path="artifacts/te_v7_stage109/fake-freeze.json"))
    assert result.artifact.status == "blocked_freeze_integrity"


def test_stage108_artifact_integrity_failure_blocks_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    def tampered(path: object) -> None:
        raise ValueError("provider execution freeze artifact integrity failure")
    monkeypatch.setattr(preflight_validator, "verify_freeze_artifact", tampered)
    result = _evaluate()
    assert result.artifact.status == "blocked_freeze_integrity"
    assert result.artifact.stage108_integrity_valid is False


def test_te_v6_manifest_path_must_be_canonical() -> None:
    result = _evaluate(_config(te_v6_manifest_path="manifests/other.json"))
    assert result.artifact.status == "blocked_frozen_invariants"


def test_production_launcher_connection_blocks_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight_validator, "_production_launcher_unconnected", lambda root: False)
    result = _evaluate()
    assert result.artifact.status == "blocked_production_connection"


def test_happy_path_is_only_eligible_for_explicit_authorization() -> None:
    result = _evaluate()
    assert result.artifact.status == "eligible_for_explicit_real_provider_authorization"
    assert result.artifact.eligible is True and result.blockers == ()


def test_happy_path_validates_stage108_and_te_v6_invariants() -> None:
    artifact = _evaluate().artifact
    assert artifact.stage108_integrity_valid is True
    assert artifact.te_v6_invariants_valid is True
    assert artifact.production_launcher_unconnected is True


def test_no_network_request_is_issued(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network request forbidden")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    assert _evaluate().artifact.network_requests == 0


def test_no_provider_or_translation_output_is_executed() -> None:
    artifact = _evaluate().artifact
    assert artifact.provider_executed is False
    assert artifact.translation_output_generated is False
    assert artifact.baseline_created is False and artifact.candidate_created is False


def test_no_comparison_or_readiness_is_evaluated() -> None:
    artifact = _evaluate().artifact
    assert artifact.comparison_executed is False
    assert artifact.readiness_evaluated is False


def test_preflight_artifact_round_trip_is_redacted() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage109" / uuid.uuid4().hex
    report = sandbox / "preflight.json"
    try:
        write_preflight_artifact(_evaluate().artifact, report, root=ROOT)
        serialized = report.read_text(encoding="utf-8")
        assert FAKE_CREDENTIAL not in serialized and AUTHORIZATION not in serialized
        verified = verify_preflight_artifact(report)
        assert verified.status == "eligible_for_explicit_real_provider_authorization"
        assert verified.network_requests == 0
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage109", ignore_errors=True)


def test_preflight_artifact_integrity_tampering_fails_closed() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage109_tamper" / uuid.uuid4().hex
    report = sandbox / "preflight.json"
    try:
        write_preflight_artifact(_evaluate().artifact, report, root=ROOT)
        payload = json.loads(report.read_text(encoding="utf-8"))
        payload["eligible"] = False
        report.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError, match="integrity failure"):
            verify_preflight_artifact(report)
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage109_tamper", ignore_errors=True)


def test_writer_rejects_execution_claims() -> None:
    artifact = replace(_evaluate().artifact, provider_executed=True)
    with pytest.raises(ValueError, match="boundary-invalid"):
        write_preflight_artifact(
            artifact,
            ROOT / ".ntpe_test_sandbox/stage109_invalid/preflight.json",
            root=ROOT,
        )


def test_writer_rejects_inconsistent_eligibility_claim() -> None:
    artifact = replace(_evaluate().artifact, eligible=False)
    with pytest.raises(ValueError, match="eligibility-invalid"):
        write_preflight_artifact(
            artifact,
            ROOT / ".ntpe_test_sandbox/stage109_invalid_eligibility/preflight.json",
            root=ROOT,
        )


def test_status_vocabulary_and_version_are_stage_local() -> None:
    required = {
        "disabled", "blocked_missing_boundary_enable", "blocked_missing_real_provider_enable",
        "blocked_missing_authorization", "blocked_missing_credential", "blocked_invalid_endpoint",
        "blocked_invalid_model", "blocked_invalid_attempt_plan", "blocked_resume_chunk",
        "blocked_artifact_path", "blocked_freeze_integrity",
        "eligible_for_explicit_real_provider_authorization",
    }
    assert required.issubset(PREFLIGHT_STATUSES)
    assert PREFLIGHT_VERSION == "7.0.0-stage10.9"


def test_artifact_path_resolver_accepts_only_stage109_json() -> None:
    target = resolve_preflight_artifact_path(
        "artifacts/te_v7_stage109/preflight.json", root=ROOT,
    )
    assert target == (ROOT / "artifacts/te_v7_stage109/preflight.json").resolve()
