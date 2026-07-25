from core.controlled_runtime_queue_admission import (
    ControlledRuntimeQueueAdmissionRequest,
)
from core.controlled_runtime_queue_admission_record_consumption import (
    ControlledRuntimeQueueAdmissionRecordConsumer,
)
from tests.unit.controlled_runtime_queue_admission_record_consumption import (
    build_context as build613_context,
)


def build_context(tmp_path, **overrides):
    upstream_root = tmp_path / "stage613"
    upstream_root.mkdir(exist_ok=True)
    context613 = build613_context(upstream_root)
    result613 = ControlledRuntimeQueueAdmissionRecordConsumer().consume(
        **context613
    )
    claim = result613.claim
    assert claim is not None

    request_values = dict(
        stage613_claim_id=claim.consumption_claim_id,
        stage613_claim_fingerprint=claim.claim_fingerprint,
        stage613_consumption_request_id=claim.consumption_request_id,
        stage613_consumption_request_fingerprint=(
            claim.consumption_request_fingerprint
        ),
        stage612_record_id=claim.record_id,
        stage612_record_fingerprint=claim.record_fingerprint,
        stage612_preparation_request_id=claim.record_request_id,
        stage612_request_fingerprint=claim.record_request_fingerprint,
        stage611_claim_id=claim.stage611_claim_id,
        stage611_claim_fingerprint=claim.stage611_claim_fingerprint,
        stage610_authorization_id=claim.authorization_id,
        stage610_decision_fingerprint=claim.decision_fingerprint,
        stage610_authorization_request_id=claim.authorization_request_id,
        stage610_request_fingerprint=(
            claim.authorization_request_fingerprint
        ),
        stage69_consumption_claim_id=claim.stage69_consumption_claim_id,
        stage69_claim_fingerprint=claim.stage69_claim_fingerprint,
        stage68_scheduling_envelope_id=claim.scheduling_envelope_id,
        stage68_envelope_fingerprint=claim.scheduling_envelope_fingerprint,
        stage67_consumption_claim_id=claim.stage67_consumption_claim_id,
        stage67_claim_fingerprint=claim.stage67_claim_fingerprint,
        stage66_scheduling_authorization_id=(
            claim.stage66_scheduling_authorization_id
        ),
        stage66_decision_fingerprint=claim.stage66_decision_fingerprint,
        runtime_boundary_id=claim.runtime_boundary_id,
        runtime_boundary_kind=claim.runtime_boundary_kind,
        selected_adapter_index=claim.selected_adapter_index,
        capability_state_fingerprint=claim.capability_state_fingerprint,
        admission_class=claim.admission_class,
        priority_class=claim.priority_class,
        ordering_key=claim.ordering_key,
        unit_scope=claim.unit_scope,
        upstream_chain=claim.canonical_chain,
    )
    request_values.update(overrides)
    request = ControlledRuntimeQueueAdmissionRequest(**request_values)
    verification_context = dict(
        stage612_record=context613["stage612_record"],
        stage612_request=context613["stage612_request"],
        stage612_result=context613["stage612_result"],
        stage612_verification_context=(
            context613["stage612_verification_context"]
        ),
    )
    return dict(
        request=request,
        stage613_claim=claim,
        stage613_request=context613["request"],
        stage613_result=result613,
        stage613_verification_context=verification_context,
        database_path=tmp_path / "stage71.sqlite3",
        allowed_root=tmp_path,
    )
