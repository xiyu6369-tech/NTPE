from __future__ import annotations

import hashlib
import inspect
import json
import shutil
import uuid
from collections.abc import Mapping
from pathlib import Path

import pytest

from core.adaptive_context_authorized_provider_harness import (
    CREDENTIAL_ENV,
    HARNESS_VERSION,
    AuthorizedProviderHarnessConfig,
    AuthorizedSingleInvocationProviderHarness,
    CallableRealAuthorizedProviderTransport,
    FakeAuthorizedProviderTransport,
    verify_authorized_harness_report,
    write_authorized_harness_report,
)
from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.adaptive_context_provider_evidence import ProviderRequestIdentity
from core.adaptive_context_real_provider_boundary import (
    ALLOWED_CREDENTIAL_ENV,
    ALLOWED_MODELS,
    ALLOWED_PROVIDER_URLS,
)

ROOT = Path(__file__).resolve().parents[2]
MODEL = "meta/llama-3.3-70b-instruct"
URL = "https://integrate.api.nvidia.com/v1/chat/completions"
HASH_A = "a" * 64
HASH_B = "b" * 64


def _config(**changes: object) -> AuthorizedProviderHarnessConfig:
    values: dict[str, object] = {
        "boundary_enabled": True,
        "real_provider_enabled": True,
        "authorization_id": "stage105-authorization",
        "execution_mode": "fake",
        "provider": "nvidia",
        "provider_url": URL,
        "model": MODEL,
        "session_id": "stage105-session",
        "single_chunk_only": True,
        "single_controlled_session": True,
    }
    values.update(changes)
    return AuthorizedProviderHarnessConfig(**values)


def _identity(**changes: object) -> ProviderRequestIdentity:
    values: dict[str, object] = {
        "pair_id": "stage105-session",
        "run_kind": "baseline",
        "set_name": "Authorized_Smoke_Set",
        "chunk_index": 1,
        "source_hash": HASH_A,
        "chunk_hash": HASH_B,
        "model": MODEL,
        "attempt": 1,
        "minimum_output_tokens": 10,
    }
    values.update(changes)
    return ProviderRequestIdentity(**values)


def _plans(*, retry: bool = False) -> tuple[ProviderAttemptPlan, ...]:
    first = ProviderAttemptPlan(1, MODEL, 30, False, 100, 80)
    if not retry:
        return (first,)
    return (first, ProviderAttemptPlan(2, MODEL, 60, True, 100, 80))


class _LeakyFakeTransport:
    provenance = "fake"

    def __init__(self) -> None:
        self.calls = 0

    def invoke(
        self, payload: Mapping[str, object], plan: ProviderAttemptPlan, *,
        provider_url: str, api_key: str,
    ) -> Mapping[str, object]:
        self.calls += 1
        return {
            "status": "success",
            "provider_model": plan.model,
            "actual_output_tokens": 20,
            "response_body": "stage105-secret-transport-response",
            "api_key": "stage105-secret-transport-credential",
        }


def _run(
    *, config: AuthorizedProviderHarnessConfig | None = None,
    harness: AuthorizedSingleInvocationProviderHarness | None = None,
    transport: FakeAuthorizedProviderTransport | None = None,
    identity: ProviderRequestIdentity | None = None,
    payload: dict[str, object] | None = None,
    plans: tuple[ProviderAttemptPlan, ...] | None = None,
):
    active = harness or AuthorizedSingleInvocationProviderHarness(config or _config())
    return active.run(
        identity=identity or _identity(),
        payload=payload or {"prompt": {"source_text": "secret-source"}},
        plans=plans or _plans(),
        transport=transport or FakeAuthorizedProviderTransport(),
        environ={"NVIDIA_API_KEY": "must-not-be-read-by-fake-transport"},
    )


def test_harness_is_disabled_by_default_and_requires_all_three_gates() -> None:
    blockers = AuthorizedProviderHarnessConfig().validate()
    assert "authorized-harness-boundary-enable-required" in blockers
    assert "authorized-harness-real-provider-enable-required" in blockers
    assert "authorized-harness-authorization-id-required" in blockers


@pytest.mark.parametrize("field,value,blocker", [
    ("boundary_enabled", False, "authorized-harness-boundary-enable-required"),
    ("real_provider_enabled", False, "authorized-harness-real-provider-enable-required"),
    ("authorization_id", "", "authorized-harness-authorization-id-required"),
])
def test_each_authorization_gate_fails_before_transport(
    field: str, value: object, blocker: str,
) -> None:
    transport = FakeAuthorizedProviderTransport()
    with pytest.raises(ValueError, match=blocker):
        _run(config=_config(**{field: value}), transport=transport)
    assert transport.calls == 0


def test_whitespace_authorization_id_is_rejected() -> None:
    assert "authorized-harness-authorization-id-required" in _config(
        authorization_id="   ",
    ).validate()


@pytest.mark.parametrize("field,value,blocker", [
    ("provider", "custom", "authorized-harness-provider-not-allowlisted"),
    ("provider_url", "https://invalid.example/v1", "authorized-harness-endpoint-not-allowlisted"),
    ("model", "unapproved-model", "authorized-harness-model-not-allowlisted"),
])
def test_stage104_provider_allowlists_are_mandatory(
    field: str, value: str, blocker: str,
) -> None:
    assert blocker in _config(**{field: value}).validate()


def test_credential_source_is_fixed_to_nvidia_environment() -> None:
    assert CREDENTIAL_ENV == "NVIDIA_API_KEY"
    assert ALLOWED_CREDENTIAL_ENV == {"nvidia": CREDENTIAL_ENV}


def test_authorized_fake_transport_creates_one_controlled_session() -> None:
    harness = AuthorizedSingleInvocationProviderHarness(_config())
    transport = FakeAuthorizedProviderTransport()
    result = _run(harness=harness, transport=transport)
    assert harness.session_claimed is True and transport.calls == 1
    assert result.authorization_confirmed is True
    assert result.execution_provenance == "fake"
    assert result.real_provider_execution is False
    assert result.invocation.session.summary.state == "completed"


def test_fake_transport_never_receives_environment_credential() -> None:
    result = _run()
    assert result.invocation.credential_source == "not_accessed"


def test_fake_and_real_transports_share_one_invocation_signature() -> None:
    fake = inspect.signature(FakeAuthorizedProviderTransport.invoke)
    real = inspect.signature(CallableRealAuthorizedProviderTransport.invoke)
    assert tuple(fake.parameters) == tuple(real.parameters)


def test_transport_provenance_must_match_execution_mode() -> None:
    transport = FakeAuthorizedProviderTransport()
    with pytest.raises(ValueError, match="transport-provenance-mismatch"):
        _run(config=_config(execution_mode="real"), transport=transport)
    assert transport.calls == 0


def test_only_chunk_one_is_admitted() -> None:
    transport = FakeAuthorizedProviderTransport()
    with pytest.raises(ValueError, match="single-chunk-identity-required"):
        _run(identity=_identity(chunk_index=2), transport=transport)
    assert transport.calls == 0


def test_session_identity_and_model_must_match_config() -> None:
    with pytest.raises(ValueError, match="session-identity-mismatch"):
        _run(identity=_identity(pair_id="other-session"))
    with pytest.raises(ValueError, match="model-identity-mismatch"):
        _run(identity=_identity(model="other-model"))


def test_one_harness_instance_cannot_create_a_second_session() -> None:
    harness = AuthorizedSingleInvocationProviderHarness(_config())
    transport = FakeAuthorizedProviderTransport()
    _run(harness=harness, transport=transport)
    with pytest.raises(ValueError, match="session-already-claimed"):
        _run(harness=harness, transport=transport)
    assert transport.calls == 1


def test_failed_invocation_still_consumes_the_single_session() -> None:
    harness = AuthorizedSingleInvocationProviderHarness(_config())
    transport = FakeAuthorizedProviderTransport(("503",))
    result = _run(harness=harness, transport=transport)
    assert result.invocation.session.summary.state == "provider_limited"
    with pytest.raises(ValueError, match="session-already-claimed"):
        _run(harness=harness, transport=transport)


def test_retry_timeout_fallback_and_per_attempt_timing_are_preserved() -> None:
    result = _run(
        transport=FakeAuthorizedProviderTransport(("timeout", "success")),
        plans=_plans(retry=True),
    )
    records = result.invocation.session.evidence.records
    assert [row.attempt for row in records] == [1, 2]
    assert records[0].error_category == "timeout"
    assert records[1].fallback_used is True
    assert all(row.timing_complete for row in records)
    assert result.invocation.session.summary.timeout_attempts == 1


def test_http_503_is_preserved_without_retry_conflation() -> None:
    result = _run(transport=FakeAuthorizedProviderTransport(("503",)))
    row = result.invocation.session.evidence.records[0]
    assert row.http_status == 503
    assert row.error_category == "http_503"
    assert result.invocation.session.summary.http_503_attempts == 1


def test_shared_boundary_sanitizes_fake_transport_response() -> None:
    transport = _LeakyFakeTransport()
    result = _run(transport=transport)  # type: ignore[arg-type]
    serialized = json.dumps(result.to_dict(), sort_keys=True)
    assert transport.calls == 1
    assert "stage105-secret-transport-response" not in serialized
    assert "stage105-secret-transport-credential" not in serialized


def test_empty_attempt_plan_does_not_create_or_execute_a_session() -> None:
    harness = AuthorizedSingleInvocationProviderHarness(_config())
    transport = FakeAuthorizedProviderTransport()
    with pytest.raises(ValueError, match="attempt-plan-required"):
        harness.run(
            identity=_identity(), payload={"prompt": "secret"}, plans=(),
            transport=transport, environ={},
        )
    assert harness.session_claimed is False and transport.calls == 0


def test_artifact_never_retains_request_prompt_response_credential_or_authorization_id() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage105_redaction" / uuid.uuid4().hex
    report = sandbox / "authorized-session.json"
    forbidden_values = (
        "stage105-secret-source", "stage105-secret-request", "stage105-secret-authorization",
        "stage105-secret-response", "stage105-secret-credential",
    )
    try:
        result = _run(
            config=_config(authorization_id="stage105-secret-authorization"),
            payload={
                "prompt": {"source_text": "stage105-secret-source"},
                "request": "stage105-secret-request",
                "response_body": "stage105-secret-response",
                "api_key": "stage105-secret-credential",
            },
        )
        write_authorized_harness_report(result, report)
        serialized = report.read_text(encoding="utf-8")
        assert all(value not in serialized for value in forbidden_values)
        verified = verify_authorized_harness_report(report)
        assert verified["request_persisted"] is False
        assert verified["prompt_persisted"] is False
        assert verified["response_body_persisted"] is False
        assert verified["credential_persisted"] is False
    finally:
        shutil.rmtree(sandbox.parent.parent, ignore_errors=True)


def test_artifact_integrity_fails_closed() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage105_integrity" / uuid.uuid4().hex
    report = sandbox / "authorized-session.json"
    try:
        write_authorized_harness_report(_run(), report)
        payload = json.loads(report.read_text(encoding="utf-8"))
        payload["session_id"] = "tampered"
        report.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError, match="integrity failure"):
            verify_authorized_harness_report(report)
    finally:
        shutil.rmtree(sandbox.parent.parent, ignore_errors=True)


def test_no_baseline_candidate_comparison_or_readiness_artifacts_are_created() -> None:
    result = _run()
    assert result.baseline_artifact_created is False
    assert result.candidate_artifact_created is False
    assert result.comparison_evaluated is False
    assert result.readiness_evaluated is False
    assert result.provider_automatically_executed is False
    assert result.invocation.comparison_evaluated is False
    assert result.invocation.readiness_evaluated is False


def test_stage104_allowlist_and_frozen_boundaries_remain_unchanged() -> None:
    targets = (
        ROOT / "core/adaptive_context_real_provider_boundary/config.py",
        ROOT / "ntpe_provider_benchmark_session.py",
        ROOT / "launcher_translate.py",
        ROOT / "lts/txt_translation_runtime.py",
        ROOT / "core/translation_runtime/runtime_speed_policy.py",
    )
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
    assert HARNESS_VERSION == "7.0.0-stage10.5"
    assert MODEL in ALLOWED_MODELS and URL in ALLOWED_PROVIDER_URLS
    _run()
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
