from core.controlled_runtime_atomic_authorization_consumption import (
    AtomicAuthorizationConsumer,
    AtomicAuthorizationConsumptionRegistry,
)
from tests.unit.controlled_runtime_atomic_authorization_consumption import build_context


def test_restart_and_independent_connection_enforce_non_reuse(tmp_path):
    context = build_context(tmp_path)
    first = AtomicAuthorizationConsumer().consume(**context)
    assert first.status == "durably_consumed_not_executed"
    restarted = AtomicAuthorizationConsumptionRegistry(context["registry"].path, tmp_path)
    context["registry"] = restarted
    duplicate = AtomicAuthorizationConsumer().consume(**context)
    assert duplicate.status == "already_consumed"
    stored = restarted.read_claim(context["request"].authorization_decision_fingerprint)
    assert stored == first.claim
    assert restarted.count_claims() == 1
