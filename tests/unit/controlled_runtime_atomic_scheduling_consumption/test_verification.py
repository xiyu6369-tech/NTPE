import pytest

from core.controlled_runtime_atomic_scheduling_consumption import (
    AtomicSchedulingAuthorizationConsumer,
    verify_atomic_scheduling_consumption_claim,
)
from core.controlled_runtime_atomic_scheduling_consumption.errors import (
    AtomicSchedulingConsumptionVerificationError,
)
from . import build_context


def verify_full(claim, context, **kwargs):
    values = dict(
        request=context["request"],
        stage66_scheduling_request=context["stage66_scheduling_request"],
        stage66_scheduling_decision=context["stage66_scheduling_decision"],
        stage65_handoff_receipt=context["stage65_handoff_receipt"],
        stage64_envelope=context["stage64_envelope"],
        stage63_claim=context["stage63_claim"],
        stage62_record=context["stage62_record"],
        authorization_decision=context["authorization_decision"],
        execution_plan=context["execution_plan"],
    )
    values.update(kwargs)
    return verify_atomic_scheduling_consumption_claim(claim, **values)


def test_authentic_claim_verifies_deterministically(tmp_path):
    context = build_context(tmp_path)
    claim = AtomicSchedulingAuthorizationConsumer().consume(**context).claim
    assert claim is not None
    first = verify_full(claim, context)
    second = verify_full(claim, context)
    assert first == second
    assert first.valid
    assert first.schema_verified
    assert first.fingerprint_verified
    assert first.request_binding_verified
    assert first.stage66_decision_binding_verified
    assert first.stage66_request_binding_verified
    assert first.stage65_binding_verified
    assert first.stage64_binding_verified
    assert first.stage63_binding_verified
    assert first.stage62_binding_verified
    assert first.stage61_binding_verified
    assert first.plan_binding_verified
    assert first.adapter_index_verified
    assert first.unit_count_verified
    assert first.runtime_boundary_verified
    assert first.upstream_chain_verified
    assert first.state_verified
    assert first.capabilities_disabled


@pytest.mark.parametrize("field,value", (
    ("claim_fingerprint", "0" * 64),
    ("scheduling_consumption_request_fingerprint", "0" * 64),
    ("stage66_scheduling_decision_fingerprint", "0" * 64),
    ("stage66_scheduling_request_fingerprint", "0" * 64),
    ("stage65_handoff_receipt_fingerprint", "0" * 64),
    ("stage64_envelope_fingerprint", "0" * 64),
    ("stage63_claim_fingerprint", "0" * 64),
    ("execution_authorization_decision_fingerprint", "0" * 64),
    ("execution_plan_fingerprint", "0" * 64),
    ("selected_adapter_index", 1),
    ("consumed_schedule_unit_count", 2),
    ("runtime_boundary_id", "other"),
    ("runtime_boundary_kind", "other"),
    ("scheduling_authorization_consumed", False),
    ("scheduling_authorization_reusable", True),
    ("durable_scheduling_reuse_prevention_established", False),
    ("persistent_scheduling_registry_written", False),
    ("runtime_execution_scheduled", True),
    ("queue_record_created", True),
    ("job_record_created", True),
    ("worker_started", True),
    ("execution_started", True),
    ("execution_completed", True),
    ("runtime_execution_enabled", True),
    ("provider_execution_enabled", True),
    ("network_execution_enabled", True),
    ("translation_execution_enabled", True),
    ("output_write_enabled", True),
    ("resume_write_enabled", True),
    ("cache_write_enabled", True),
    ("retry_enabled", True),
    ("fallback_enabled", True),
    ("production_hook_enabled", True),
))
def test_tampered_claim_fails_closed(tmp_path, field, value):
    context = build_context(tmp_path)
    claim = AtomicSchedulingAuthorizationConsumer().consume(**context).claim
    assert claim is not None
    object.__setattr__(claim, field, value)
    verification = verify_full(claim, context)
    assert not verification.valid
    assert verification.reason_codes


def test_tampered_chain_fails_closed(tmp_path):
    context = build_context(tmp_path)
    claim = AtomicSchedulingAuthorizationConsumer().consume(**context).claim
    chain = list(claim.upstream_fingerprint_chain)
    chain[3] = "0" * 64
    object.__setattr__(claim, "upstream_fingerprint_chain", tuple(chain))
    verification = verify_full(claim, context)
    assert not verification.valid
    assert "CLAIM_FINGERPRINT_MISMATCH" in verification.reason_codes


def test_raise_on_error_uses_dedicated_verification_error(tmp_path):
    context = build_context(tmp_path)
    claim = AtomicSchedulingAuthorizationConsumer().consume(**context).claim
    object.__setattr__(claim, "claim_fingerprint", "0" * 64)
    with pytest.raises(AtomicSchedulingConsumptionVerificationError):
        verify_full(claim, context, raise_on_error=True)