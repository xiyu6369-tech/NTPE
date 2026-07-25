from core.controlled_runtime_queue_admission_record import (
    ControlledRuntimeQueueAdmissionRecordBuilder,
)
from core.controlled_runtime_queue_admission_record_consumption import (
    ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
)
from core.controlled_runtime_queue_admission_record.serialization import canonical_sha256
from tests.unit.controlled_runtime_queue_admission_record import (
    build_context as build612_context,
)


def build_context(tmp_path, **overrides):
    c612 = build612_context(tmp_path)
    builder = ControlledRuntimeQueueAdmissionRecordBuilder()
    stage612_result = builder.prepare(**c612)
    record = stage612_result.record
    assert record is not None

    ordering_key = canonical_sha256({
        "admission_class": record.admission_class,
        "priority_class": record.priority_class,
        "record_id": record.queue_admission_record_id,
    })

    vals = dict(
        record_id=record.queue_admission_record_id,
        record_fingerprint=record.record_fingerprint,
        record_request_id=c612["request"].record_request_id,
        record_request_fingerprint=c612["request"].request_fingerprint,
        consumption_claim_id=record.consumption_claim_id,
        claim_fingerprint=record.claim_fingerprint,
        upstream_consumption_request_id=record.consumption_request_id,
        consumption_request_fingerprint=record.consumption_request_fingerprint,
        authorization_id=record.authorization_id,
        decision_fingerprint=record.decision_fingerprint,
        authorization_request_id=record.authorization_request_id,
        authorization_request_fingerprint=record.authorization_request_fingerprint,
        stage69_consumption_claim_id=record.stage69_consumption_claim_id,
        stage69_claim_fingerprint=record.stage69_claim_fingerprint,
        scheduling_envelope_id=record.scheduling_envelope_id,
        scheduling_envelope_fingerprint=record.scheduling_envelope_fingerprint,
        stage67_consumption_claim_id=record.stage67_consumption_claim_id,
        stage67_claim_fingerprint=record.stage67_claim_fingerprint,
        stage66_scheduling_authorization_id=record.stage66_scheduling_authorization_id,
        stage66_decision_fingerprint=record.stage66_decision_fingerprint,
        runtime_boundary_id=record.runtime_boundary_id,
        runtime_boundary_kind=record.runtime_boundary_kind,
        selected_adapter_index=record.selected_adapter_index,
        capability_state_fingerprint=record.capability_state_fingerprint,
        unit_scope=1,
        admission_class=record.admission_class,
        priority_class=record.priority_class,
        ordering_key=ordering_key,
        upstream_chain=record.canonical_chain,
    )
    vals.update(overrides)
    request = ControlledRuntimeQueueAdmissionRecordConsumptionRequest(**vals)

    vctx = dict(
        stage611_claim=c612["stage611_claim"],
        stage611_request=c612["stage611_request"],
        stage611_result=c612["stage611_result"],
        stage611_verification_context=c612["stage611_verification_context"],
    )
    return dict(
        request=request,
        stage612_record=record,
        stage612_request=c612["request"],
        stage612_result=stage612_result,
        stage612_verification_context=vctx,
        database_path=tmp_path / "stage613.sqlite3",
        allowed_root=tmp_path,
    )