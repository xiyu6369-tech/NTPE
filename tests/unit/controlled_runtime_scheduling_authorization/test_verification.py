from dataclasses import replace

import pytest

from core.controlled_runtime_scheduling_authorization import (
    verify_scheduling_authorization_decision,
)
from core.controlled_runtime_scheduling_authorization.errors import (
    ControlledRuntimeSchedulingAuthorizationVerificationError,
)
from tests.unit.controlled_runtime_scheduling_authorization.test_authorizer import (
    authorize,
    build_inputs,
)


def verify(inputs, decision, **kwargs):
    return verify_scheduling_authorization_decision(
        decision, request=inputs["request"],
        execution_plan=inputs["execution_plan"],
        authorization_request=inputs["authorization_request"],
        authorization_decision=inputs["authorization_decision"],
        stage62_request=inputs["stage62_request"],
        stage62_record=inputs["stage62_record"],
        stage63_claim_request=inputs["stage63_claim_request"],
        stage63_claim=inputs["stage63_claim"],
        stage64_envelope_request=inputs["stage64_envelope_request"],
        stage64_envelope=inputs["stage64_envelope"],
        stage65_handoff_request=inputs["stage65_handoff_request"],
        stage65_handoff_receipt=inputs["stage65_handoff_receipt"], **kwargs,
    )


def test_authentic_decision_verifies_deterministically():
    inputs = build_inputs()
    decision = authorize(inputs).decision
    first = verify(inputs, decision)
    second = verify(inputs, decision)
    assert first.valid and first == second


@pytest.mark.parametrize("field,value,reason", (
    ("scheduling_authorization_request_fingerprint", "0" * 64,
     "REQUEST_BINDING_MISMATCH"),
    ("stage65_handoff_receipt_fingerprint", "0" * 64,
     "HANDOFF_BINDING_MISMATCH"),
    ("stage65_handoff_request_fingerprint", "0" * 64,
     "HANDOFF_BINDING_MISMATCH"),
    ("stage64_envelope_fingerprint", "0" * 64,
     "ENVELOPE_BINDING_MISMATCH"),
    ("stage63_claim_fingerprint", "0" * 64, "CLAIM_BINDING_MISMATCH"),
    ("authorization_id", "other", "AUTHORIZATION_BINDING_MISMATCH"),
    ("execution_plan_fingerprint", "0" * 64, "PLAN_BINDING_MISMATCH"),
    ("selected_adapter_index", 1, "ADAPTER_INDEX_MISMATCH"),
    ("authorized_schedule_unit_count", 2, "UNIT_COUNT_MISMATCH"),
    ("runtime_boundary_id", "other", "RUNTIME_BOUNDARY_MISMATCH"),
    ("runtime_boundary_kind", "other", "RUNTIME_BOUNDARY_MISMATCH"),
    ("scheduling_authorized", False, "DECISION_STATE_INVALID"),
    ("scheduling_authorization_consumed", True, "DECISION_STATE_INVALID"),
    ("scheduling_authorization_reusable", True, "DECISION_STATE_INVALID"),
    ("schedule_once", False, "DECISION_STATE_INVALID"),
    ("runtime_execution_scheduled", True, "DECISION_STATE_INVALID"),
    ("queue_record_created", True, "DECISION_STATE_INVALID"),
    ("job_record_created", True, "DECISION_STATE_INVALID"),
    ("worker_started", True, "DECISION_STATE_INVALID"),
    ("execution_started", True, "DECISION_STATE_INVALID"),
    ("execution_completed", True, "DECISION_STATE_INVALID"),
    ("runtime_execution_enabled", True, "CAPABILITY_ENABLED"),
    ("provider_execution_enabled", True, "CAPABILITY_ENABLED"),
    ("network_execution_enabled", True, "CAPABILITY_ENABLED"),
    ("translation_execution_enabled", True, "CAPABILITY_ENABLED"),
    ("output_write_enabled", True, "CAPABILITY_ENABLED"),
    ("resume_write_enabled", True, "CAPABILITY_ENABLED"),
    ("cache_write_enabled", True, "CAPABILITY_ENABLED"),
    ("retry_enabled", True, "CAPABILITY_ENABLED"),
    ("fallback_enabled", True, "CAPABILITY_ENABLED"),
    ("production_hook_enabled", True, "CAPABILITY_ENABLED"),
))
def test_tampered_decision_fails(field, value, reason):
    inputs = build_inputs()
    decision = replace(authorize(inputs).decision, **{field: value})
    checked = verify(inputs, decision)
    assert not checked.valid
    assert reason in checked.reason_codes


def test_raw_fingerprint_and_chain_tampering_fail_and_can_raise():
    inputs = build_inputs()
    decision = authorize(inputs).decision
    object.__setattr__(decision, "decision_fingerprint", "0" * 64)
    checked = verify(inputs, decision)
    assert not checked.valid
    assert "DECISION_FINGERPRINT_MISMATCH" in checked.reason_codes
    assert "UPSTREAM_CHAIN_MISMATCH" in checked.reason_codes
    with pytest.raises(
        ControlledRuntimeSchedulingAuthorizationVerificationError
    ):
        verify(inputs, decision, raise_on_error=True)
