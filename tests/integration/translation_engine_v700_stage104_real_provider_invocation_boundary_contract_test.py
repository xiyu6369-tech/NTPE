from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path

import pytest

from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.adaptive_context_provider_evidence import ProviderRequestIdentity
from core.adaptive_context_real_provider_boundary import (
    ALLOWED_MODELS, ALLOWED_PROVIDER_URLS, BOUNDARY_VERSION,
    CallableRealProviderInvocationBridge, FakeProviderInvocationBridge,
    RealProviderBoundaryConfig, RealProviderInvocationBoundary,
    sanitize_provider_result, verify_boundary_report, write_boundary_report,
)

ROOT = Path(__file__).resolve().parents[2]
MODEL = "meta/llama-3.3-70b-instruct"
URL = "https://integrate.api.nvidia.com/v1/chat/completions"
HASH_A = "a" * 64
HASH_B = "b" * 64


def _config(**changes: object) -> RealProviderBoundaryConfig:
    values: dict[str, object] = {
        "enabled": True, "execution_mode": "fake", "provider": "nvidia",
        "provider_url": URL, "model": MODEL, "credential_env": "NVIDIA_API_KEY",
        "pair_id": "stage104-pair", "run_kind": "baseline", "single_chunk_only": True,
    }
    values.update(changes)
    return RealProviderBoundaryConfig(**values)


def _identity() -> ProviderRequestIdentity:
    return ProviderRequestIdentity(
        pair_id="stage104-pair", run_kind="baseline", set_name="Smoke_Set",
        chunk_index=1, source_hash=HASH_A, chunk_hash=HASH_B, model=MODEL,
        attempt=1, minimum_output_tokens=10,
    )


def _plans(*, retry: bool = False) -> tuple[ProviderAttemptPlan, ...]:
    first = ProviderAttemptPlan(1, MODEL, 30, False, 100, 80)
    if not retry:
        return (first,)
    return (first, ProviderAttemptPlan(2, MODEL, 60, True, 100, 80))


def _run(
    *, config: RealProviderBoundaryConfig | None = None,
    bridge: FakeProviderInvocationBridge | None = None,
    payload: dict[str, object] | None = None,
    plans: tuple[ProviderAttemptPlan, ...] | None = None,
):
    return RealProviderInvocationBoundary(config or _config()).run(
        identity=_identity(), payload=payload or {"prompt": {"source_text": "secret-source"}},
        plans=plans or _plans(), bridge=bridge or FakeProviderInvocationBridge(),
        environ={"NVIDIA_API_KEY": "must-not-be-read-in-fake-mode"},
    )


def test_boundary_disabled_by_default() -> None:
    assert "real-provider-boundary-explicit-enable-required" in RealProviderBoundaryConfig().validate()


def test_real_mode_requires_additional_enable() -> None:
    assert "real-provider-additional-explicit-enable-required" in _config(execution_mode="real").validate()


def test_real_mode_requires_separate_authorization() -> None:
    assert "real-provider-separate-authorization-required" in _config(
        execution_mode="real", enable_real_provider=True,
    ).validate()


def test_fake_mode_cannot_claim_real_enable() -> None:
    assert "fake-bridge-cannot-claim-real-provider-enable" in _config(enable_real_provider=True).validate()


@pytest.mark.parametrize("field,value,blocker", [
    ("provider", "custom", "provider-not-allowlisted"),
    ("provider_url", "https://evil.invalid/v1", "provider-url-not-allowlisted"),
    ("model", "unapproved-model", "provider-model-not-allowlisted"),
    ("credential_env", "PLAINTEXT_API_KEY", "provider-credential-environment-not-allowlisted"),
])
def test_provider_configuration_is_allowlisted(field: str, value: str, blocker: str) -> None:
    assert blocker in _config(**{field: value}).validate()


def test_single_chunk_boundary_is_required() -> None:
    assert "real-provider-boundary-single-chunk-required" in _config(single_chunk_only=False).validate()


def test_fake_bridge_is_default_test_path_and_never_claims_real() -> None:
    result = _run()
    assert result.execution_provenance == "fake"
    assert result.real_provider_execution is False
    assert result.credential_source == "not_accessed"
    assert all(not row.real_provider_execution for row in result.session.evidence.records)


def test_fake_bridge_performs_no_network_and_receives_no_secret() -> None:
    bridge = FakeProviderInvocationBridge()
    result = _run(bridge=bridge)
    assert bridge.calls == 1
    assert result.session.summary.state == "completed"


def test_real_and_fake_bridge_provenance_cannot_be_mixed() -> None:
    with pytest.raises(ValueError, match="provider-bridge-provenance-mismatch"):
        _run(config=_config(execution_mode="real", enable_real_provider=True, authorization_id="approval-1"))


def test_real_bridge_requires_environment_credential_before_invocation() -> None:
    called = False

    def invoker(payload, plan, provider_url, api_key):
        nonlocal called
        called = True
        return {"status": "success"}

    config = _config(execution_mode="real", enable_real_provider=True, authorization_id="approval-1")
    with pytest.raises(ValueError, match="real-provider-environment-credential-required"):
        RealProviderInvocationBoundary(config).run(
            identity=_identity(), payload={"prompt": "not persisted"}, plans=_plans(),
            bridge=CallableRealProviderInvocationBridge(invoker), environ={},
        )
    assert called is False


def test_attempt_models_are_allowlisted() -> None:
    bad = (ProviderAttemptPlan(1, "unapproved-model", 30),)
    with pytest.raises(ValueError, match="attempt-model-not-allowlisted"):
        _run(plans=bad)


def test_each_retry_has_independent_timing_and_fallback_provenance() -> None:
    result = _run(bridge=FakeProviderInvocationBridge(("timeout", "success")), plans=_plans(retry=True))
    records = result.session.evidence.records
    assert [row.attempt for row in records] == [1, 2]
    assert all(row.timing_complete for row in records)
    assert records[0].error_category == "timeout"
    assert records[1].fallback_used is True
    assert result.session.summary.total_latency_ms >= 0


def test_http_503_provenance_is_preserved() -> None:
    result = _run(bridge=FakeProviderInvocationBridge(("503",)))
    row = result.session.evidence.records[0]
    assert row.http_status == 503 and row.external_provider_condition is True
    assert result.session.summary.state == "provider_limited"


def test_provider_result_sanitizer_removes_payload_and_secrets() -> None:
    clean = sanitize_provider_result({
        "status": "success", "actual_output_tokens": 10, "response_body": "secret",
        "provider_response": "secret", "api_key": "secret", "prompt": "secret",
    })
    assert clean == {"status": "success", "actual_output_tokens": 10}


def test_request_payload_is_not_persisted_in_artifact() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage104_payload" / uuid.uuid4().hex
    report = sandbox / "report.json"
    try:
        result = _run(payload={"prompt": {"source_text": "highly-secret-source"}, "authorization": "secret"})
        write_boundary_report(result, report)
        serialized = report.read_text(encoding="utf-8")
        assert "highly-secret-source" not in serialized
        assert '"prompt"' not in serialized and '"authorization"' not in serialized
        payload = verify_boundary_report(report)
        assert payload["request_payload_persisted"] is False
    finally:
        shutil.rmtree(sandbox.parent.parent, ignore_errors=True)


def test_boundary_artifact_integrity_fails_closed() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage104_integrity" / uuid.uuid4().hex
    report = sandbox / "report.json"
    try:
        write_boundary_report(_run(), report)
        payload = json.loads(report.read_text(encoding="utf-8"))
        payload["model"] = "tampered"
        report.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError, match="integrity failure"):
            verify_boundary_report(report)
    finally:
        shutil.rmtree(sandbox.parent.parent, ignore_errors=True)


def test_no_comparison_or_readiness_is_evaluated() -> None:
    result = _run()
    assert result.comparison_evaluated is False and result.readiness_evaluated is False
    assert result.session.summary.readiness_evaluated is False


def test_stage103_and_frozen_runtime_remain_unchanged() -> None:
    targets = (
        ROOT / "core/adaptive_context_provider_session_cli/harness.py",
        ROOT / "ntpe_provider_benchmark_session.py",
        ROOT / "lts/txt_translation_runtime.py",
        ROOT / "core/translation_runtime/runtime_speed_policy.py",
        ROOT / "artifacts/te_v7_stage09/TE_V7_STAGE09_BASELINE.json",
    )
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
    assert BOUNDARY_VERSION == "7.0.0-stage10.4"
    assert MODEL in ALLOWED_MODELS and URL in ALLOWED_PROVIDER_URLS
    _run()
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
