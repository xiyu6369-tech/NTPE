from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from core.controlled_runtime_queue_admission_record_consumption import (
    ControlledRuntimeQueueAdmissionRecordConsumer,
    ControlledRuntimeQueueAdmissionRecordConsumptionRegistry,
)
from tests.unit.controlled_runtime_queue_admission_record_consumption import (
    build_context,
)


def test_six_concurrent_consumers_produce_exactly_one_claim(tmp_path):
    context = build_context(tmp_path)
    barrier = Barrier(6)

    def consume(_):
        barrier.wait()
        return ControlledRuntimeQueueAdmissionRecordConsumer().consume(
            **dict(context)
        )

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(consume, range(6)))

    assert sum(result.claim is not None for result in results) == 1
    assert sum(result.verification_succeeded for result in results) == 1
    assert sum(result.replay_detected for result in results) == 5
    assert sum(result.record_consumption_count for result in results) == 1
    registry = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_claims() == 1
