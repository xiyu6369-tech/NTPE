from core.controlled_runtime_queue_admission import ControlledRuntimeQueueAdmitter
from core.controlled_runtime_scheduling_dispatch import (
    ControlledRuntimeSchedulingRequest,
)
from tests.unit.controlled_runtime_queue_admission import (
    build_context as build71_context,
)


def build_context(tmp_path, **overrides):
    upstream_root = tmp_path / "stage71"
    upstream_root.mkdir(exist_ok=True)
    context71 = build71_context(upstream_root)
    result71 = ControlledRuntimeQueueAdmitter().admit(**context71)
    record = result71.queue_record
    assert record is not None
    request_values = dict(
        queue_record_id=record.queue_record_id,
        queue_record_fingerprint=record.queue_record_fingerprint,
        admission_request_id=record.admission_request_id,
        admission_request_fingerprint=record.admission_request_fingerprint,
        stage613_claim_id=record.stage613_claim_id,
        stage613_claim_fingerprint=record.stage613_claim_fingerprint,
        stage612_record_id=record.stage612_record_id,
        stage612_record_fingerprint=record.stage612_record_fingerprint,
        stage611_claim_id=record.stage611_claim_id,
        stage611_claim_fingerprint=record.stage611_claim_fingerprint,
        stage610_authorization_id=record.stage610_authorization_id,
        stage610_decision_fingerprint=record.stage610_decision_fingerprint,
        stage69_consumption_claim_id=record.stage69_consumption_claim_id,
        stage69_claim_fingerprint=record.stage69_claim_fingerprint,
        stage68_scheduling_envelope_id=record.stage68_scheduling_envelope_id,
        stage68_envelope_fingerprint=record.stage68_envelope_fingerprint,
        stage67_consumption_claim_id=record.stage67_consumption_claim_id,
        stage67_claim_fingerprint=record.stage67_claim_fingerprint,
        stage66_scheduling_authorization_id=(
            record.stage66_scheduling_authorization_id
        ),
        stage66_decision_fingerprint=record.stage66_decision_fingerprint,
        runtime_boundary_id=record.runtime_boundary_id,
        runtime_boundary_kind=record.runtime_boundary_kind,
        selected_adapter_index=record.selected_adapter_index,
        capability_state_fingerprint=record.capability_state_fingerprint,
        admission_class=record.admission_class,
        priority_class=record.priority_class,
        ordering_key=record.ordering_key,
        unit_scope=record.unit_scope,
        execution_plan_reference_fingerprint=record.canonical_chain[6],
        work_package_reference_fingerprint=record.canonical_chain[0],
        upstream_chain=record.canonical_chain,
    )
    request_values.update(overrides)
    request = ControlledRuntimeSchedulingRequest(**request_values)
    return dict(
        request=request,
        queue_record=record,
        stage71_request=context71["request"],
        stage71_result=result71,
        stage613_claim=context71["stage613_claim"],
        stage613_request=context71["stage613_request"],
        stage613_result=context71["stage613_result"],
        stage613_verification_context=(
            context71["stage613_verification_context"]
        ),
        database_path=tmp_path / "stage72.sqlite3",
        allowed_root=tmp_path,
    )
