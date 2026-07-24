from core.controlled_runtime_atomic_scheduling_consumption import (
    AtomicSchedulingAuthorizationConsumptionRequest,
)
from core.controlled_runtime_atomic_scheduling_consumption.policy import (
    REGISTRY_NAMESPACE,
    exact_consumption_scope,
)
from core.controlled_runtime_scheduling_authorization import (
    ControlledRuntimeSchedulingAuthorizer,
)
from tests.unit.controlled_runtime_scheduling_authorization.test_authorizer import (
    build_inputs as build_stage66_inputs,
)


def build_request(stage66_inputs, stage66_result, **overrides):
    decision = stage66_result.decision
    assert decision is not None
    values = dict(
        scheduling_consumption_id="schedule-consume-001",
        scheduling_authorization_id=decision.scheduling_authorization_id,
        handoff_id=decision.handoff_id,
        envelope_id=decision.envelope_id,
        claim_id=decision.claim_id,
        consumption_id=decision.consumption_id,
        authorization_id=decision.authorization_id,
        execution_plan_fingerprint=decision.execution_plan_fingerprint,
        execution_authorization_decision_fingerprint=
            decision.execution_authorization_decision_fingerprint,
        stage63_claim_fingerprint=decision.stage63_claim_fingerprint,
        stage64_envelope_fingerprint=decision.stage64_envelope_fingerprint,
        stage65_handoff_receipt_fingerprint=
            decision.stage65_handoff_receipt_fingerprint,
        stage66_scheduling_request_fingerprint=
            stage66_inputs["request"].request_fingerprint,
        stage66_scheduling_decision_fingerprint=decision.decision_fingerprint,
        selected_adapter_index=decision.selected_adapter_index,
        requested_schedule_unit_count=1,
        runtime_boundary_id=decision.runtime_boundary_id,
        runtime_boundary_kind=decision.runtime_boundary_kind,
        consume_scheduling_authorization=True,
        caller_confirmation=True,
        queue_creation_requested=False,
        job_creation_requested=False,
        worker_start_requested=False,
        runtime_execution_requested=False,
        provider_execution_requested=False,
        translation_execution_requested=False,
        consumption_scope="pending",
        registry_namespace=REGISTRY_NAMESPACE,
        purpose="Stage 6.7 測試\r\nmetadata",
    )
    values.update(overrides)
    if "consumption_scope" not in overrides:
        values["consumption_scope"] = exact_consumption_scope(
            **{
                name: values[name]
                for name in (
                    "scheduling_authorization_id",
                    "handoff_id",
                    "envelope_id",
                    "claim_id",
                    "consumption_id",
                    "authorization_id",
                    "execution_plan_fingerprint",
                    "execution_authorization_decision_fingerprint",
                    "stage63_claim_fingerprint",
                    "stage64_envelope_fingerprint",
                    "stage65_handoff_receipt_fingerprint",
                    "stage66_scheduling_request_fingerprint",
                    "stage66_scheduling_decision_fingerprint",
                    "selected_adapter_index",
                    "runtime_boundary_id",
                    "runtime_boundary_kind",
                )
            }
        )
    return AtomicSchedulingAuthorizationConsumptionRequest(**values)


def build_context(tmp_path, **request_overrides):
    stage66_inputs = build_stage66_inputs()
    stage66_result = ControlledRuntimeSchedulingAuthorizer().authorize(
        **stage66_inputs
    )
    context = dict(stage66_inputs)
    stage66_request = context.pop("request")
    context.update(
        request=build_request(
            stage66_inputs, stage66_result, **request_overrides
        ),
        stage66_scheduling_request=stage66_request,
        stage66_scheduling_decision=stage66_result.decision,
        stage66_scheduling_result=stage66_result,
        allowed_root=tmp_path,
        database_path=tmp_path / "stage67.sqlite3",
    )
    return context