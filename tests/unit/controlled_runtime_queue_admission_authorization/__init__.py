from core.controlled_runtime_queue_admission_authorization import (
    ControlledRuntimeQueueAdmissionAuthorizationRequest,
)
from core.controlled_runtime_queue_admission_authorization.serialization import (
    canonical_sha256,
)
from core.controlled_runtime_scheduling_envelope_consumption import (
    ControlledRuntimeSchedulingEnvelopeConsumer,
)
from tests.unit.controlled_runtime_scheduling_envelope_consumption import (
    build_context as build_stage69_context,
)


def build_context(tmp_path, **overrides):
    upstream = build_stage69_context(tmp_path)
    stage69_result = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**upstream)
    claim = stage69_result.claim
    assert claim is not None
    stage69_request = upstream["request"]
    capability = canonical_sha256({
        "execution_started": False,
        "network_execution": False,
        "provider_execution": False,
        "queue_record_created": False,
        "runtime_execution_scheduled": False,
        "translation_execution": False,
    })
    values = dict(
        stage69_consumption_claim_id=claim.consumption_claim_id,
        stage69_claim_fingerprint=claim.claim_fingerprint,
        stage69_consumption_request_id=stage69_request.consumption_request_id,
        stage69_request_fingerprint=stage69_request.request_fingerprint,
        scheduling_envelope_id=claim.scheduling_envelope_id,
        scheduling_envelope_fingerprint=claim.scheduling_envelope_fingerprint,
        stage67_consumption_claim_id=claim.stage67_consumption_claim_id,
        stage67_claim_fingerprint=claim.stage67_claim_fingerprint,
        stage66_scheduling_authorization_id=claim.stage66_scheduling_authorization_id,
        stage66_decision_fingerprint=claim.stage66_decision_fingerprint,
        runtime_boundary_id=claim.runtime_boundary_id,
        runtime_boundary_kind=claim.runtime_boundary_kind,
        selected_adapter_index=claim.selected_adapter_index,
        capability_state_fingerprint=capability,
        unit_scope=1,
        upstream_chain=claim.canonical_chain,
    )
    values.update(overrides)
    request = ControlledRuntimeQueueAdmissionAuthorizationRequest(**values)
    verification_context = {
        key: upstream[key] for key in (
            "scheduling_envelope", "scheduling_envelope_request",
            "stage67_scheduling_consumption_request",
            "stage67_scheduling_consumption_claim",
            "stage66_scheduling_decision", "stage65_handoff_receipt",
            "stage64_envelope", "stage63_claim", "stage62_record",
            "authorization_decision", "execution_plan",
        )
    }
    verification_context.update(
        persisted_payload_json=claim.to_json(),
        persistence_committed=True,
    )
    return dict(
        request=request, stage69_claim=claim, stage69_request=stage69_request,
        stage69_result=stage69_result,
        stage69_verification_context=verification_context,
    )
