from core.controlled_runtime_atomic_scheduling_consumption import (
    AtomicSchedulingAuthorizationConsumer,
    AtomicSchedulingAuthorizationConsumptionRegistry,
    verify_atomic_scheduling_consumption_claim,
)
from tests.unit.controlled_runtime_atomic_scheduling_consumption import build_context


def test_complete_authentic_stage53_through_stage67_contract(tmp_path):
    context = build_context(tmp_path)
    before = tuple(repr(value) for value in context.values())
    result = AtomicSchedulingAuthorizationConsumer().consume(**context)
    after = tuple(repr(value) for value in context.values())
    assert before == after
    assert result.status == "scheduling_authorization_consumed_not_scheduled"
    assert result.claim is not None
    assert len(result.claim.upstream_fingerprint_chain) == 21
    assert result.claim.upstream_fingerprint_chain[:19] == (
        context["stage66_scheduling_decision"].upstream_fingerprint_chain
    )
    verification = verify_atomic_scheduling_consumption_claim(
        result.claim,
        request=context["request"],
        stage66_scheduling_request=context["stage66_scheduling_request"],
        stage66_scheduling_decision=context["stage66_scheduling_decision"],
        stage65_handoff_receipt=context["stage65_handoff_receipt"],
        stage64_envelope=context["stage64_envelope"],
        stage63_claim=context["stage63_claim"],
        stage62_record=context["stage62_record"],
        authorization_decision=context["authorization_decision"],
        execution_plan=context["execution_plan"],
    )
    assert verification.valid
    registry = AtomicSchedulingAuthorizationConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_claims() == 1
    assert registry.read(result.claim.scheduling_consumption_id) == result.claim


def test_consumption_does_not_imply_scheduling_queue_or_execution(tmp_path):
    result = AtomicSchedulingAuthorizationConsumer().consume(**build_context(tmp_path))
    assert result.claim.scheduling_authorization_consumed is True
    assert result.claim.runtime_execution_scheduled is False
    assert result.claim.queue_record_created is False
    assert result.claim.job_record_created is False
    assert result.claim.worker_started is False
    assert result.claim.execution_started is False
    assert result.claim.execution_completed is False
    assert result.scheduler_invoked is False
    assert result.queue_written is False
    assert result.runtime_invoked is False


def test_complete_integration_is_deterministic(tmp_path):
    left_context = build_context(tmp_path)
    left_context["database_path"] = tmp_path / "left.sqlite3"
    right_context = build_context(tmp_path)
    right_context["database_path"] = tmp_path / "right.sqlite3"
    left = AtomicSchedulingAuthorizationConsumer().consume(**left_context)
    right = AtomicSchedulingAuthorizationConsumer().consume(**right_context)
    assert left == right