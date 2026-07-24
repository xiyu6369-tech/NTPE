from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from core.controlled_runtime_atomic_scheduling_consumption import (
    AtomicSchedulingAuthorizationConsumer,
    AtomicSchedulingAuthorizationConsumptionRegistry,
    verify_atomic_scheduling_consumption_claim,
)
from tests.unit.controlled_runtime_atomic_scheduling_consumption import build_context


def test_two_independent_connections_produce_exactly_one_claim(tmp_path):
    context = build_context(tmp_path)
    barrier = Barrier(2)

    def attempt():
        local = dict(context)
        barrier.wait()
        return AtomicSchedulingAuthorizationConsumer().consume(**local)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))

    assert sorted(result.status for result in results) == [
        "already_consumed",
        "scheduling_authorization_consumed_not_scheduled",
    ]
    successes = [result for result in results if result.claim is not None]
    assert len(successes) == 1
    registry = AtomicSchedulingAuthorizationConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_claims() == 1
    committed = registry.read(context["request"].scheduling_consumption_id)
    assert committed == successes[0].claim
    assert verify_atomic_scheduling_consumption_claim(
        committed, request=context["request"]
    ).valid