from core.controlled_runtime_execution_plan import (
    validate_controlled_runtime_preparation_freeze,
)
from core.controlled_runtime_scheduling_authorization import (
    ControlledRuntimeSchedulingAuthorizer,
    verify_scheduling_authorization_decision,
)
from tests.unit.controlled_runtime_scheduling_authorization.test_authorizer import (
    build_inputs,
)


def test_complete_authentic_stage53_through_stage66_contract():
    inputs = build_inputs()
    inputs["freeze_validation"] = (
        validate_controlled_runtime_preparation_freeze()
    )
    before = tuple(repr(value) for value in inputs.values())
    result = ControlledRuntimeSchedulingAuthorizer().authorize(**inputs)
    after = tuple(repr(value) for value in inputs.values())
    assert before == after
    assert result.status == "scheduling_authorized_not_consumed_not_scheduled"
    assert len(result.decision.upstream_fingerprint_chain) == 19
    verified = verify_scheduling_authorization_decision(
        result.decision, request=inputs["request"],
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
        stage65_handoff_receipt=inputs["stage65_handoff_receipt"],
    )
    assert verified.valid


def test_authorization_is_not_consumption_scheduling_or_execution():
    result = ControlledRuntimeSchedulingAuthorizer().authorize(**build_inputs())
    decision = result.decision
    assert decision.scheduling_authorized is True
    assert decision.scheduling_authorization_consumed is False
    assert decision.runtime_execution_scheduled is False
    assert decision.queue_record_created is False
    assert decision.execution_started is False
    assert result.scheduler_invoked is False
    assert result.runtime_invoked is False


def test_complete_integration_is_deterministic():
    left = ControlledRuntimeSchedulingAuthorizer().authorize(**build_inputs())
    right = ControlledRuntimeSchedulingAuthorizer().authorize(**build_inputs())
    assert left == right
