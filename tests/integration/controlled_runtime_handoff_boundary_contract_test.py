from core.controlled_runtime_execution_plan import (
    validate_controlled_runtime_preparation_freeze,
)
from core.controlled_runtime_handoff_boundary import (
    ControlledRuntimeHandoffBoundary,
    verify_runtime_handoff_receipt,
)
from tests.unit.controlled_runtime_handoff_boundary.test_boundary import build_inputs


def test_complete_authentic_stage53_through_stage65_contract():
    inputs = build_inputs()
    inputs["freeze_validation"] = validate_controlled_runtime_preparation_freeze()
    before = tuple(repr(value) for value in inputs.values())
    result = ControlledRuntimeHandoffBoundary().accept(**inputs)
    after = tuple(repr(value) for value in inputs.values())
    assert before == after
    assert result.status == "handoff_accepted_not_scheduled_not_executed"
    assert len(result.receipt.upstream_fingerprint_chain) == 17
    assert result.receipt.upstream_fingerprint_chain[:15] == (
        inputs["stage64_envelope"].upstream_fingerprint_chain
    )
    verified = verify_runtime_handoff_receipt(
        result.receipt, request=inputs["request"],
        execution_plan=inputs["execution_plan"],
        authorization_request=inputs["authorization_request"],
        authorization_decision=inputs["authorization_decision"],
        stage62_request=inputs["stage62_request"],
        stage62_record=inputs["stage62_record"],
        stage63_claim_request=inputs["stage63_claim_request"],
        stage63_claim=inputs["stage63_claim"],
        stage64_envelope_request=inputs["stage64_envelope_request"],
        stage64_envelope=inputs["stage64_envelope"],
    )
    assert verified.valid
    assert result.receipt.runtime_handoff_completed is True
    assert result.receipt.runtime_execution_scheduled is False
    assert result.receipt.execution_started is False
    assert result.runtime_invoked is False


def test_complete_integration_is_deterministic():
    left = ControlledRuntimeHandoffBoundary().accept(**build_inputs())
    right = ControlledRuntimeHandoffBoundary().accept(**build_inputs())
    assert left.receipt == right.receipt
    assert left.result_fingerprint == right.result_fingerprint
