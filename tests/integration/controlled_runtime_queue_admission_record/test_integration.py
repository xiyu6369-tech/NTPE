from core.controlled_runtime_queue_admission_record import (
    ControlledRuntimeQueueAdmissionRecordBuilder,
)
from tests.unit.controlled_runtime_queue_admission_record import build_context


def test_authentic_end_to_end_record_preparation_has_no_side_effects(tmp_path):
    result = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**build_context(tmp_path))
    assert result.verification_succeeded and result.record_preparation_count == 1
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
