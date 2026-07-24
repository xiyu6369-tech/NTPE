from core.controlled_runtime_queue_admission_authorization import (
    ControlledRuntimeQueueAdmissionAuthorizer,
)
from tests.unit.controlled_runtime_queue_admission_authorization import build_context


def test_authentic_end_to_end_authorization_has_no_side_effects(tmp_path):
    result = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**build_context(tmp_path))
    assert result.authorized and result.decision_count == 1
    assert (
        result.queue_admission_count,
        result.queue_record_count,
        result.scheduler_access_count,
        result.runtime_execution_count,
        result.provider_execution_count,
        result.network_execution_count,
        result.translation_execution_count,
    ) == (0, 0, 0, 0, 0, 0, 0)
