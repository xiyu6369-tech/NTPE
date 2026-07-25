from core.controlled_runtime_queue_admission import (
    ControlledRuntimeQueueAdmitter,
    ControlledRuntimeQueueRegistry,
)
from tests.unit.controlled_runtime_queue_admission import build_context


def test_authentic_stage613_claim_creates_one_verified_durable_queue_record(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmitter().admit(**context)
    record = result.queue_record
    assert result.upstream_verified
    assert result.persistence_committed
    assert result.durable_readback_verified
    assert result.queue_admission_performed
    assert result.queue_record_created
    assert record is not None
    assert len(record.canonical_chain) == 35
    assert tuple(record.canonical_chain[:33]) == tuple(
        context["stage613_claim"].canonical_chain
    )
    registry = ControlledRuntimeQueueRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_records() == 1
    assert registry.read(context["request"].admission_request_id) == record


def test_replay_and_binding_conflict_preserve_exactly_one_original_record(tmp_path):
    context = build_context(tmp_path)
    admitter = ControlledRuntimeQueueAdmitter()
    first = admitter.admit(**context)
    original = first.queue_record
    assert original is not None
    replay = admitter.admit(**context)
    assert replay.replay_detected
    assert replay.queue_record is None
    object.__setattr__(context["request"], "ordering_key", "conflicting-order")
    conflict = admitter.admit(**context)
    assert not conflict.verification_succeeded
    assert conflict.queue_record is None
    registry = ControlledRuntimeQueueRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_records() == 1
    assert registry.read(first.request.admission_request_id) == original


def test_complete_zero_side_effect_audit_beyond_queue_admission(tmp_path):
    result = ControlledRuntimeQueueAdmitter().admit(**build_context(tmp_path))
    record = result.queue_record
    assert record is not None
    assert not record.runtime_execution_scheduled
    assert not record.execution_started
    assert (
        result.runtime_schedule_count,
        result.scheduler_count,
        result.task_created_count,
        result.job_created_count,
        result.worker_created_count,
        result.runtime_execution_count,
        result.provider_execution_count,
        result.network_execution_count,
        result.translation_execution_count,
        result.output_write_count,
        result.resume_write_count,
        result.cache_write_count,
    ) == (0,) * 12
    assert (result.queue_admission_count, result.queue_record_created_count) == (1, 1)
