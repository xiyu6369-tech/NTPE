from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from core.controlled_runtime_scheduling_dispatch import (
    ControlledRuntimeScheduler,
    ControlledRuntimeSchedulingRegistry,
)
from tests.unit.controlled_runtime_scheduling_dispatch import build_context


def test_authentic_stage71_to_schedule_dispatch_and_replay(tmp_path):
    context = build_context(tmp_path)
    first = ControlledRuntimeScheduler().schedule(**context)
    replay = ControlledRuntimeScheduler().schedule(**context)
    assert first.verification_succeeded
    assert len(first.dispatch_package.canonical_chain) == 38
    assert replay.replay_detected
    assert ControlledRuntimeSchedulingRegistry(
        context["database_path"], allowed_root=tmp_path
    ).counts() == (1, 1, 1)
    assert (
        first.runtime_execution_count,
        first.worker_started_count,
        first.provider_execution_count,
        first.network_execution_count,
        first.translation_execution_count,
        first.output_write_count,
        first.resume_write_count,
        first.cache_write_count,
    ) == (0, 0, 0, 0, 0, 0, 0, 0)


def test_six_way_concurrency_exactly_one_success(tmp_path):
    context = build_context(tmp_path)
    barrier = Barrier(6)

    def attempt(_):
        barrier.wait()
        return ControlledRuntimeScheduler().schedule(**context)

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(attempt, range(6)))
    assert sum(result.verification_succeeded for result in results) == 1
    assert sum(result.replay_detected for result in results) == 5
    assert ControlledRuntimeSchedulingRegistry(
        context["database_path"], allowed_root=tmp_path
    ).counts() == (1, 1, 1)
