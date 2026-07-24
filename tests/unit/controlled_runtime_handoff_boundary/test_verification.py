from dataclasses import replace

import pytest

from core.controlled_runtime_handoff_boundary.errors import (
    ControlledRuntimeHandoffVerificationError,
)
from core.controlled_runtime_handoff_boundary import verify_runtime_handoff_receipt
from tests.unit.controlled_runtime_handoff_boundary.test_boundary import (
    accept,
    build_inputs,
)


def verify(inputs, receipt, **kwargs):
    return verify_runtime_handoff_receipt(
        receipt, request=inputs["request"],
        execution_plan=inputs["execution_plan"],
        authorization_request=inputs["authorization_request"],
        authorization_decision=inputs["authorization_decision"],
        stage62_request=inputs["stage62_request"],
        stage62_record=inputs["stage62_record"],
        stage63_claim_request=inputs["stage63_claim_request"],
        stage63_claim=inputs["stage63_claim"],
        stage64_envelope_request=inputs["stage64_envelope_request"],
        stage64_envelope=inputs["stage64_envelope"], **kwargs,
    )


def test_authentic_receipt_verifies_deterministically():
    inputs = build_inputs()
    receipt = accept(inputs).receipt
    first = verify(inputs, receipt)
    second = verify(inputs, receipt)
    assert first.valid and second == first


@pytest.mark.parametrize("field,value,reason", (
    ("handoff_request_fingerprint", "0" * 64, "REQUEST_BINDING_MISMATCH"),
    ("stage64_envelope_fingerprint", "0" * 64, "ENVELOPE_BINDING_MISMATCH"),
    ("stage63_claim_fingerprint", "0" * 64, "CLAIM_BINDING_MISMATCH"),
    ("authorization_id", "other", "AUTHORIZATION_BINDING_MISMATCH"),
    ("execution_plan_fingerprint", "0" * 64, "PLAN_BINDING_MISMATCH"),
    ("runtime_boundary_id", "other", "RUNTIME_BOUNDARY_MISMATCH"),
    ("runtime_boundary_kind", "other", "RUNTIME_BOUNDARY_MISMATCH"),
    ("selected_adapter_index", 1, "ADAPTER_INDEX_MISMATCH"),
    ("accepted_unit_count", 2, "UNIT_COUNT_MISMATCH"),
    ("authorization_reusable", True, "RECEIPT_STATE_INVALID"),
    ("durable_reuse_prevention_established", False, "RECEIPT_STATE_INVALID"),
    ("persistent_registry_written", False, "RECEIPT_STATE_INVALID"),
    ("runtime_handoff_prepared", False, "RECEIPT_STATE_INVALID"),
    ("runtime_handoff_completed", False, "RECEIPT_STATE_INVALID"),
    ("runtime_boundary_accepted", False, "RECEIPT_STATE_INVALID"),
    ("runtime_execution_scheduled", True, "RECEIPT_STATE_INVALID"),
    ("execution_started", True, "RECEIPT_STATE_INVALID"),
    ("execution_completed", True, "RECEIPT_STATE_INVALID"),
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
def test_tampered_receipt_fails(field, value, reason):
    inputs = build_inputs()
    receipt = replace(accept(inputs).receipt, **{field: value})
    checked = verify(inputs, receipt)
    assert not checked.valid
    assert reason in checked.reason_codes


def test_raw_fingerprint_and_chain_tampering_fail_and_can_raise():
    inputs = build_inputs()
    receipt = accept(inputs).receipt
    object.__setattr__(receipt, "receipt_fingerprint", "0" * 64)
    checked = verify(inputs, receipt)
    assert not checked.valid
    assert "RECEIPT_FINGERPRINT_MISMATCH" in checked.reason_codes
    assert "UPSTREAM_CHAIN_MISMATCH" in checked.reason_codes
    with pytest.raises(ControlledRuntimeHandoffVerificationError):
        verify(inputs, receipt, raise_on_error=True)
