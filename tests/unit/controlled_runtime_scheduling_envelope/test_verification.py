import pytest

from core.controlled_runtime_scheduling_envelope import (
    ControlledRuntimeSchedulingEnvelopeBuilder,
    verify_controlled_runtime_scheduling_envelope,
)
from core.controlled_runtime_scheduling_envelope.errors import (
    ControlledRuntimeSchedulingEnvelopeVerificationError,
)
from . import build_context


def verify_full(envelope, context, **overrides):
    values = dict(
        request=context["request"],
        stage67_scheduling_consumption_request=
            context["stage67_scheduling_consumption_request"],
        stage67_scheduling_consumption_claim=
            context["stage67_scheduling_consumption_claim"],
        stage66_scheduling_decision=
            context["stage66_scheduling_decision"],
        stage65_handoff_receipt=context["stage65_handoff_receipt"],
        stage64_envelope=context["stage64_envelope"],
        stage63_claim=context["stage63_claim"],
        stage62_record=context["stage62_record"],
        authorization_decision=context["authorization_decision"],
        execution_plan=context["execution_plan"],
    )
    values.update(overrides)
    return verify_controlled_runtime_scheduling_envelope(envelope, **values)


def test_authentic_envelope_verifies_deterministically(tmp_path):
    context = build_context(tmp_path)
    envelope = ControlledRuntimeSchedulingEnvelopeBuilder().build(
        **context
    ).scheduling_envelope
    first = verify_full(envelope, context)
    second = verify_full(envelope, context)
    assert first == second
    assert first.valid
    assert first.schema_verified
    assert first.fingerprint_verified
    assert first.request_binding_verified
    assert first.stage67_binding_verified
    assert first.stage66_binding_verified
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


@pytest.mark.parametrize(
    "field,value",
    (
        ("scheduling_envelope_fingerprint", "0" * 64),
        ("scheduling_envelope_request_fingerprint", "0" * 64),
        (
            "stage67_scheduling_consumption_claim_fingerprint",
            "0" * 64,
        ),
        (
            "stage67_scheduling_consumption_request_fingerprint",
            "0" * 64,
        ),
        ("stage66_scheduling_decision_fingerprint", "0" * 64),
        ("stage65_handoff_receipt_fingerprint", "0" * 64),
        ("stage64_envelope_fingerprint", "0" * 64),
        ("stage63_claim_fingerprint", "0" * 64),
        ("execution_authorization_decision_fingerprint", "0" * 64),
        ("execution_plan_fingerprint", "0" * 64),
        ("selected_adapter_index", 1),
        ("schedule_unit_count", 2),
        ("runtime_boundary_id", "other"),
        ("runtime_boundary_kind", "other"),
        ("scheduling_envelope_prepared", False),
        ("scheduling_envelope_consumed", True),
        ("scheduling_envelope_reusable", True),
        ("queue_admission_authorized", True),
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
    ),
)
def test_tampered_envelope_fails_closed(tmp_path, field, value):
    context = build_context(tmp_path)
    envelope = ControlledRuntimeSchedulingEnvelopeBuilder().build(
        **context
    ).scheduling_envelope
    object.__setattr__(envelope, field, value)
    result = verify_full(envelope, context)
    assert not result.valid
    assert result.reason_codes


def test_tampered_chain_fails_closed(tmp_path):
    context = build_context(tmp_path)
    envelope = ControlledRuntimeSchedulingEnvelopeBuilder().build(
        **context
    ).scheduling_envelope
    chain = list(envelope.upstream_fingerprint_chain)
    chain[4] = "0" * 64
    object.__setattr__(envelope, "upstream_fingerprint_chain", tuple(chain))
    result = verify_full(envelope, context)
    assert not result.valid
    assert "ENVELOPE_FINGERPRINT_MISMATCH" in result.reason_codes


def test_raise_on_error_uses_dedicated_error(tmp_path):
    context = build_context(tmp_path)
    envelope = ControlledRuntimeSchedulingEnvelopeBuilder().build(
        **context
    ).scheduling_envelope
    object.__setattr__(
        envelope,
        "scheduling_envelope_fingerprint",
        "0" * 64,
    )
    with pytest.raises(ControlledRuntimeSchedulingEnvelopeVerificationError):
        verify_full(envelope, context, raise_on_error=True)
