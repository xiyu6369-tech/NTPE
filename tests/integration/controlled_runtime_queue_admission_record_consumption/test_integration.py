from core.controlled_runtime_queue_admission_record_consumption import (
    ControlledRuntimeQueueAdmissionRecordConsumer,
    ControlledRuntimeQueueAdmissionRecordConsumptionRegistry,
)
from tests.unit.controlled_runtime_queue_admission_record_consumption import (
    build_context,
)


def test_authentic_stage612_record_is_durably_consumed_without_admission(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
    claim = result.claim

    assert result.upstream_verified
    assert result.persistence_committed
    assert result.durable_readback_verified
    assert result.durable_claim_created
    assert result.exactly_one_record_consumed
    assert claim is not None
    assert claim.queue_admission_record_prepared
    assert claim.queue_admission_record_consumed
    assert not claim.queue_admission_record_reusable
    assert len(claim.canonical_chain) == 33
    registry = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.read(context["request"].consumption_request_id) == claim
    assert (
        result.queue_admission_count,
        result.queue_record_created_count,
        result.queue_record_consumed_count,
        result.scheduling_queued_count,
        result.scheduler_count,
        result.runtime_execution_count,
        result.provider_execution_count,
        result.network_execution_count,
        result.translation_execution_count,
    ) == (0, 0, 0, 0, 0, 0, 0, 0, 0)
