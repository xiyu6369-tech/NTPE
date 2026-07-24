from core.controlled_runtime_queue_admission_authorization_consumption import (
    ControlledRuntimeQueueAdmissionAuthorizationConsumer,
)
from core.controlled_runtime_queue_admission_record import (
    ControlledRuntimeQueueAdmissionRecordRequest,
)
from core.controlled_runtime_queue_admission_record.serialization import canonical_sha256
from tests.unit.controlled_runtime_queue_admission_authorization_consumption import (
    build_context as build611_context,
)

def build_context(tmp_path, **overrides):
    c611 = build611_context(tmp_path)
    consumer = ControlledRuntimeQueueAdmissionAuthorizationConsumer()
    stage611_result = consumer.consume(**dict(c611))
    claim = stage611_result.claim
    assert claim is not None
    stage611_request = c611["request"]
    capability = canonical_sha256({
        "execution_started": False,
        "network_execution": False,
        "provider_execution": False,
        "queue_record_created": False,
        "runtime_execution_scheduled": False,
        "translation_execution": False,
    })
    vals = dict(
        consumption_claim_id=claim.consumption_claim_id,
        claim_fingerprint=claim.claim_fingerprint,
        consumption_request_id=claim.consumption_request_id,
        consumption_request_fingerprint=claim.consumption_request_fingerprint,
        authorization_id=claim.authorization_id,
        decision_fingerprint=claim.decision_fingerprint,
        authorization_request_id=claim.authorization_request_id,
        authorization_request_fingerprint=claim.authorization_request_fingerprint,
        stage69_consumption_claim_id=claim.stage69_consumption_claim_id,
        stage69_claim_fingerprint=claim.stage69_claim_fingerprint,
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
    vals.update(overrides)
    request = ControlledRuntimeQueueAdmissionRecordRequest(**vals)
    vctx = dict(
        stage610_decision=c611["stage610_decision"],
        stage610_request=c611["stage610_request"],
        stage610_result=c611["stage610_result"],
        stage610_verification_context=c611["stage610_verification_context"],
        persisted_payload_json=claim.to_json(),
        persistence_committed=True,
    )
    return dict(
        request=request,
        stage611_claim=claim,
        stage611_request=stage611_request,
        stage611_result=stage611_result,
        stage611_verification_context=vctx,
    )
