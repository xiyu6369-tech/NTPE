"""Tests for Stage 6.4 models — immutability, schemas, public API."""

import hashlib
from typing import get_type_hints

import pytest

from core.controlled_runtime_execution_envelope import (
    ControlledRuntimeExecutionEnvelope,
    ControlledRuntimeExecutionEnvelopeRequest,
    ControlledRuntimeExecutionEnvelopeResult,
    ControlledRuntimeExecutionEnvelopePolicy,
    ControlledRuntimeExecutionEnvelopeBuilder,
    verify_execution_envelope,
    __all__,
)
from core.controlled_runtime_execution_envelope.models import (
    ControlledRuntimeExecutionEnvelopeFinding,
    canonical_sha256,
)


def _fp(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Request model tests
# ---------------------------------------------------------------------------


def test_request_is_frozen():
    req = ControlledRuntimeExecutionEnvelopeRequest(
        envelope_id="env-001",
        claim_id="claim-001",
        consumption_id="cons-001",
        authorization_id="auth-001",
        authorization_request_fingerprint=_fp("ar"),
        authorization_decision_fingerprint=_fp("ad"),
        execution_plan_fingerprint=_fp("ep"),
        stage62_request_fingerprint=_fp("62r"),
        stage62_record_fingerprint=_fp("62c"),
        stage63_claim_request_fingerprint=_fp("63cr"),
        stage63_claim_fingerprint=_fp("63c"),
        selected_adapter_index=0,
        requested_unit_count=1,
        runtime_handoff_requested=True,
        caller_confirmation=True,
        runtime_scope="exact auth/claim/plan/adapter/unit",
        execution_mode="controlled_single_execution",
        purpose="acceptance test",
    )
    with pytest.raises(Exception):
        req.envelope_id = "changed"  # type: ignore


def test_request_schema():
    req = ControlledRuntimeExecutionEnvelopeRequest(
        envelope_id="env-001",
        claim_id="claim-001",
        consumption_id="cons-001",
        authorization_id="auth-001",
        authorization_request_fingerprint=_fp("ar"),
        authorization_decision_fingerprint=_fp("ad"),
        execution_plan_fingerprint=_fp("ep"),
        stage62_request_fingerprint=_fp("62r"),
        stage62_record_fingerprint=_fp("62c"),
        stage63_claim_request_fingerprint=_fp("63cr"),
        stage63_claim_fingerprint=_fp("63c"),
        selected_adapter_index=0,
        requested_unit_count=1,
        runtime_handoff_requested=True,
        caller_confirmation=True,
        runtime_scope="exact scope",
        execution_mode="controlled_single_execution",
        purpose="test",
    )
    assert req.schema_name == "ntpe.controlled_runtime_execution_envelope_request"
    assert req.schema_version == "1.0"


def test_request_fingerprint_present():
    req = ControlledRuntimeExecutionEnvelopeRequest(
        envelope_id="env-001",
        claim_id="claim-001",
        consumption_id="cons-001",
        authorization_id="auth-001",
        authorization_request_fingerprint=_fp("ar"),
        authorization_decision_fingerprint=_fp("ad"),
        execution_plan_fingerprint=_fp("ep"),
        stage62_request_fingerprint=_fp("62r"),
        stage62_record_fingerprint=_fp("62c"),
        stage63_claim_request_fingerprint=_fp("63cr"),
        stage63_claim_fingerprint=_fp("63c"),
        selected_adapter_index=0,
        requested_unit_count=1,
        runtime_handoff_requested=True,
        caller_confirmation=True,
        runtime_scope="exact scope",
        execution_mode="controlled_single_execution",
        purpose="test",
    )
    assert isinstance(req.request_fingerprint, str)
    assert len(req.request_fingerprint) == 64


# ---------------------------------------------------------------------------
# Envelope model tests
# ---------------------------------------------------------------------------


def _make_valid_envelope() -> ControlledRuntimeExecutionEnvelope:
    chain = tuple(_fp(f"layer{i}") for i in range(14))
    return ControlledRuntimeExecutionEnvelope(
        envelope_id="env-001",
        claim_id="claim-001",
        consumption_id="cons-001",
        authorization_id="auth-001",
        authorization_request_fingerprint=_fp("ar"),
        authorization_decision_fingerprint=_fp("ad"),
        execution_plan_fingerprint=_fp("ep"),
        stage62_request_fingerprint=_fp("62r"),
        stage62_record_fingerprint=_fp("62c"),
        stage63_claim_request_fingerprint=_fp("63cr"),
        stage63_claim_fingerprint=_fp("63c"),
        selected_adapter_index=0,
        execution_unit_count=1,
        authorization_consumption_prepared=True,
        authorization_consumed=True,
        authorization_reusable=False,
        durable_reuse_prevention_established=True,
        persistent_registry_written=True,
        runtime_handoff_prepared=True,
        runtime_handoff_completed=False,
        execution_started=False,
        execution_completed=False,
        runtime_execution_enabled=False,
        provider_execution_enabled=False,
        network_execution_enabled=False,
        translation_execution_enabled=False,
        output_write_enabled=False,
        resume_write_enabled=False,
        cache_write_enabled=False,
        retry_enabled=False,
        fallback_enabled=False,
        production_hook_enabled=False,
        execution_mode="controlled_single_execution",
        envelope_state="runtime_handoff_prepared_not_executed",
        upstream_fingerprint_chain=chain,
        envelope_request_fingerprint=_fp("req-fp"),
    )


def test_envelope_is_frozen():
    env = _make_valid_envelope()
    with pytest.raises(Exception):
        env.envelope_id = "changed"  # type: ignore


def test_envelope_schema():
    env = _make_valid_envelope()
    assert env.schema_name == "ntpe.controlled_runtime_execution_envelope"
    assert env.schema_version == "1.0"


def test_envelope_fingerprint_present():
    env = _make_valid_envelope()
    assert isinstance(env.envelope_fingerprint, str)
    assert len(env.envelope_fingerprint) == 64


def test_envelope_success_state_bools_correct():
    env = _make_valid_envelope()
    assert env.authorization_consumption_prepared is True
    assert env.authorization_consumed is True
    assert env.authorization_reusable is False
    assert env.durable_reuse_prevention_established is True
    assert env.persistent_registry_written is True
    assert env.runtime_handoff_prepared is True
    assert env.runtime_handoff_completed is False
    assert env.execution_started is False
    assert env.execution_completed is False
    assert env.runtime_execution_enabled is False
    assert env.provider_execution_enabled is False
    assert env.network_execution_enabled is False
    assert env.translation_execution_enabled is False
    assert env.output_write_enabled is False
    assert env.resume_write_enabled is False
    assert env.cache_write_enabled is False
    assert env.retry_enabled is False
    assert env.fallback_enabled is False
    assert env.production_hook_enabled is False


def test_envelope_execution_mode_and_state():
    env = _make_valid_envelope()
    assert env.execution_mode == "controlled_single_execution"
    assert env.envelope_state == "runtime_handoff_prepared_not_executed"


def test_envelope_unit_count_exactly_one():
    env = _make_valid_envelope()
    assert env.execution_unit_count == 1
    assert isinstance(env.execution_unit_count, int)


# ---------------------------------------------------------------------------
# Result model tests
# ---------------------------------------------------------------------------


def _make_valid_result() -> ControlledRuntimeExecutionEnvelopeResult:
    env = _make_valid_envelope()
    req = ControlledRuntimeExecutionEnvelopeRequest(
        envelope_id="env-001",
        claim_id="claim-001",
        consumption_id="cons-001",
        authorization_id="auth-001",
        authorization_request_fingerprint=_fp("ar"),
        authorization_decision_fingerprint=_fp("ad"),
        execution_plan_fingerprint=_fp("ep"),
        stage62_request_fingerprint=_fp("62r"),
        stage62_record_fingerprint=_fp("62c"),
        stage63_claim_request_fingerprint=_fp("63cr"),
        stage63_claim_fingerprint=_fp("63c"),
        selected_adapter_index=0,
        requested_unit_count=1,
        runtime_handoff_requested=True,
        caller_confirmation=True,
        runtime_scope="test",
        execution_mode="controlled_single_execution",
        purpose="test",
    )
    return ControlledRuntimeExecutionEnvelopeResult(
        request=req,
        envelope=env,
        freeze_gate_verified=True,
        execution_plan_verified=True,
        authorization_request_verified=True,
        authorization_decision_verified=True,
        stage62_request_verified=True,
        stage62_record_verified=True,
        stage62_result_verified=True,
        stage63_claim_request_verified=True,
        stage63_claim_verified=True,
        stage63_result_verified=True,
        authorization_binding_verified=True,
        consumption_binding_verified=True,
        durable_claim_binding_verified=True,
        execution_unit_verified=True,
        runtime_scope_verified=True,
        policy_findings=(),
        status="runtime_handoff_prepared_not_executed",
        recommended_action="retain_for_controlled_runtime_handoff",
    )


def test_result_is_frozen():
    r = _make_valid_result()
    with pytest.raises(Exception):
        r.status = "changed"  # type: ignore


def test_result_success_defaults():
    r = _make_valid_result()
    assert r.runtime_invoked is False
    assert r.provider_invoked is False
    assert r.network_invoked is False
    assert r.translation_invoked is False
    assert r.output_written is False
    assert r.resume_written is False
    assert r.cache_written is False
    assert r.retry_used is False
    assert r.fallback_used is False
    assert r.production_hook_invoked is False


# ---------------------------------------------------------------------------
# Finding model tests
# ---------------------------------------------------------------------------


def test_finding_is_frozen():
    f = ControlledRuntimeExecutionEnvelopeFinding(
        code="TEST_CODE",
        severity="error",
        message="test",
        field="test_field",
        expected="expected_value",
        observed="observed_value",
    )
    with pytest.raises(Exception):
        f.code = "changed"  # type: ignore


def test_findings_tuple_immutable():
    f1 = ControlledRuntimeExecutionEnvelopeFinding(
        code="F1", severity="info", message="m1", field="f", expected="e", observed="o")
    f2 = ControlledRuntimeExecutionEnvelopeFinding(
        code="F2", severity="info", message="m2", field="f", expected="e", observed="o")
    t = (f1, f2)
    with pytest.raises(Exception):
        t[0] = f2  # type: ignore


# ---------------------------------------------------------------------------
# Public API tests
# ---------------------------------------------------------------------------


def test_exact_public_api_exports():
    expected = {
        "ControlledRuntimeExecutionEnvelopeRequest",
        "ControlledRuntimeExecutionEnvelope",
        "ControlledRuntimeExecutionEnvelopeResult",
        "ControlledRuntimeExecutionEnvelopePolicy",
        "ControlledRuntimeExecutionEnvelopeBuilder",
        "verify_execution_envelope",
    }
    assert set(__all__) == expected


def test_all_exports_importable():
    for name in __all__:
        obj = getattr(
            __import__("core.controlled_runtime_execution_envelope", fromlist=[name]),
            name,
        )
        assert obj is not None


# ---------------------------------------------------------------------------
# Canonical serialization tests
# ---------------------------------------------------------------------------


def test_canonical_sha256_deterministic():
    data = '{"a":1,"b":2}'.encode("utf-8")
    h1 = canonical_sha256(data)
    h2 = canonical_sha256(data)
    assert h1 == h2
    assert len(h1) == 64


def test_canonical_sha256_sensitive_to_ordering():
    h1 = canonical_sha256(b'{"a":1,"b":2}')
    h2 = canonical_sha256(b'{"b":2,"a":1}')
    assert h1 != h2  # Different JSON order -> different hash