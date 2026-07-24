from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from core.controlled_runtime_scheduling_envelope_consumption import (
    ControlledRuntimeSchedulingEnvelopeConsumer,
    ControlledRuntimeSchedulingEnvelopeConsumptionRegistry,
)
from tests.unit.controlled_runtime_scheduling_envelope_consumption import (
    build_context,
)


def test_concurrent_consumers_create_exactly_one_claim(tmp_path):
    context = build_context(tmp_path)
    barrier = Barrier(6)

    def attempt():
        barrier.wait()
        return ControlledRuntimeSchedulingEnvelopeConsumer().consume(
            **dict(context)
        )

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: attempt(), range(6)))
    successes = [result for result in results if result.claim is not None]
    replays = [result for result in results if result.replay_detected]
    assert len(successes) == 1
    assert len(replays) == 5
    assert all(
        result.status
        in {
            "scheduling_envelope_consumed_not_admitted_not_scheduled",
            "already_consumed",
        }
        for result in results
    )
    registry = ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_claims() == 1
    assert registry.read(
        context["request"].consumption_request_id
    ) == successes[0].claim
