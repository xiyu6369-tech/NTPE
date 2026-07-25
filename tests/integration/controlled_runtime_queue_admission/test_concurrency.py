from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from core.controlled_runtime_queue_admission import (
    ControlledRuntimeQueueAdmitter,
    ControlledRuntimeQueueRegistry,
)
from tests.unit.controlled_runtime_queue_admission import build_context


def test_six_independent_concurrent_admitters_create_exactly_one_record(tmp_path):
    context = build_context(tmp_path)
    barrier = Barrier(6)

    def admit(_):
        barrier.wait()
        return ControlledRuntimeQueueAdmitter().admit(**dict(context))

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(admit, range(6)))

    successes = [result for result in results if result.queue_record is not None]
    failures = [result for result in results if result.queue_record is None]
    assert len(successes) == 1
    assert len(failures) == 5
    assert sum(result.verification_succeeded for result in results) == 1
    assert sum(result.replay_detected for result in results) == 5
    assert sum(result.queue_admission_count for result in results) == 1
    assert sum(result.queue_record_created_count for result in results) == 1
    assert all("REGISTRY_ERROR" not in result.reason_codes for result in results)
    registry = ControlledRuntimeQueueRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_records() == 1
    stored = registry.read(context["request"].admission_request_id)
    assert stored == successes[0].queue_record
