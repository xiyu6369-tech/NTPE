from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from core.controlled_runtime_atomic_authorization_consumption import (
    AtomicAuthorizationConsumer,
    AtomicAuthorizationConsumptionRegistry,
)
from tests.unit.controlled_runtime_atomic_authorization_consumption import build_context


def test_two_overlapping_connections_produce_one_claim(tmp_path):
    context = build_context(tmp_path)
    barrier = Barrier(2)

    def attempt():
        local = dict(context)
        local["registry"] = AtomicAuthorizationConsumptionRegistry(context["registry"].path, tmp_path)
        barrier.wait()
        return AtomicAuthorizationConsumer().consume(**local)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(result.status for result in results) == [
        "already_consumed", "durably_consumed_not_executed"
    ]
    assert AtomicAuthorizationConsumptionRegistry(context["registry"].path, tmp_path).count_claims() == 1
