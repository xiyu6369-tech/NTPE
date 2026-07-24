from core.controlled_runtime_atomic_scheduling_consumption import (
    AtomicSchedulingAuthorizationConsumer,
)
from core.controlled_runtime_scheduling_envelope import (
    ControlledRuntimeSchedulingEnvelopeRequest,
)
from core.controlled_runtime_scheduling_envelope.policy import (
    exact_scheduling_scope,
)
from tests.unit.controlled_runtime_atomic_scheduling_consumption import (
    build_context as build_stage67_context,
)


def build_request(stage67_request, stage67_claim, **overrides):
    values = dict(
        scheduling_envelope_id="scheduling-envelope-001",
        scheduling_consumption_id=stage67_claim.scheduling_consumption_id,
        scheduling_authorization_id=
            stage67_claim.scheduling_authorization_id,
        handoff_id=stage67_claim.handoff_id,
        envelope_id=stage67_claim.envelope_id,
        claim_id=stage67_claim.claim_id,
        consumption_id=stage67_claim.consumption_id,
        authorization_id=stage67_claim.authorization_id,
        execution_plan_fingerprint=
            stage67_claim.execution_plan_fingerprint,
        execution_authorization_decision_fingerprint=
            stage67_claim.execution_authorization_decision_fingerprint,
        stage63_claim_fingerprint=stage67_claim.stage63_claim_fingerprint,
        stage64_envelope_fingerprint=
            stage67_claim.stage64_envelope_fingerprint,
        stage65_handoff_receipt_fingerprint=
            stage67_claim.stage65_handoff_receipt_fingerprint,
        stage66_scheduling_request_fingerprint=
            stage67_claim.stage66_scheduling_request_fingerprint,
        stage66_scheduling_decision_fingerprint=
            stage67_claim.stage66_scheduling_decision_fingerprint,
        stage67_scheduling_consumption_request_fingerprint=
            stage67_request.request_fingerprint,
        stage67_scheduling_consumption_claim_fingerprint=
            stage67_claim.claim_fingerprint,
        selected_adapter_index=stage67_claim.selected_adapter_index,
        requested_schedule_unit_count=1,
        runtime_boundary_id=stage67_claim.runtime_boundary_id,
        runtime_boundary_kind=stage67_claim.runtime_boundary_kind,
        prepare_scheduling_envelope=True,
        caller_confirmation=True,
        queue_admission_requested=False,
        queue_write_requested=False,
        job_creation_requested=False,
        worker_start_requested=False,
        runtime_execution_requested=False,
        provider_execution_requested=False,
        translation_execution_requested=False,
        scheduling_scope="pending",
        purpose="Stage 6.8 測試\r\nmetadata",
    )
    values.update(overrides)
    if "scheduling_scope" not in overrides:
        values["scheduling_scope"] = exact_scheduling_scope(
            **{
                name: values[name]
                for name in (
                    "scheduling_consumption_id",
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
                    "stage67_scheduling_consumption_request_fingerprint",
                    "stage67_scheduling_consumption_claim_fingerprint",
                    "selected_adapter_index",
                    "runtime_boundary_id",
                    "runtime_boundary_kind",
                )
            }
        )
    return ControlledRuntimeSchedulingEnvelopeRequest(**values)


def build_context(tmp_path, **request_overrides):
    stage67_context = build_stage67_context(tmp_path)
    stage67_result = AtomicSchedulingAuthorizationConsumer().consume(
        **stage67_context
    )
    stage67_claim = stage67_result.claim
    assert stage67_claim is not None
    stage67_request = stage67_context.pop("request")
    stage67_context.pop("allowed_root")
    stage67_context.pop("database_path")
    stage67_context.update(
        request=build_request(
            stage67_request,
            stage67_claim,
            **request_overrides,
        ),
        stage67_scheduling_consumption_request=stage67_request,
        stage67_scheduling_consumption_claim=stage67_claim,
        stage67_scheduling_consumption_result=stage67_result,
    )
    return stage67_context
