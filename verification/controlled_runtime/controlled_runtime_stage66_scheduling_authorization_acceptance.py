"""Offline acceptance check for Stage 6.6."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.controlled_runtime_scheduling_authorization import (
    ControlledRuntimeSchedulingAuthorizer,
    verify_scheduling_authorization_decision,
)
from tests.unit.controlled_runtime_scheduling_authorization.test_authorizer import (
    build_inputs,
)


def main() -> int:
    inputs = build_inputs()
    result = ControlledRuntimeSchedulingAuthorizer().authorize(**inputs)
    decision = result.decision
    assert result.status == "scheduling_authorized_not_consumed_not_scheduled"
    assert decision is not None
    assert decision.scheduling_authorized
    assert not decision.scheduling_authorization_consumed
    assert not decision.runtime_execution_scheduled
    assert not decision.queue_record_created
    assert not decision.execution_started
    assert len(decision.upstream_fingerprint_chain) == 19
    checked = verify_scheduling_authorization_decision(
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
        stage65_handoff_receipt=inputs["stage65_handoff_receipt"],
    )
    assert checked.valid
    print("Stage 6.6 scheduling authorization: AUTHORIZED")
    print("Authorizer calls: 1 (pure in-memory)")
    print("Decisions: 1; consumptions/scheduling/execution/writes: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
