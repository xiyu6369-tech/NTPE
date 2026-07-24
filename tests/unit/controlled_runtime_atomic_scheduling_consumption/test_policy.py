from dataclasses import FrozenInstanceError

import pytest

from core.controlled_runtime_atomic_scheduling_consumption import (
    AtomicSchedulingAuthorizationConsumptionPolicy,
)
from core.controlled_runtime_atomic_scheduling_consumption.policy import (
    DEFAULT_POLICY,
    exact_consumption_scope,
)
from . import build_context


def test_policy_is_exact_and_immutable():
    assert DEFAULT_POLICY.complete_chain_layers == 21
    assert DEFAULT_POLICY.consumed_schedule_unit_count == 1
    assert DEFAULT_POLICY.maximum_provider_requests == 1
    assert DEFAULT_POLICY.maximum_translation_requests == 1
    assert DEFAULT_POLICY.maximum_retries == 0
    assert DEFAULT_POLICY.maximum_fallbacks == 0
    with pytest.raises(FrozenInstanceError):
        DEFAULT_POLICY.complete_chain_layers = 22


def test_scope_is_canonical_and_binds_runtime_kind(tmp_path):
    request = build_context(tmp_path)["request"]
    assert '"runtime_boundary_kind":"controlled_offline_acceptance_boundary"' in request.consumption_scope
    values = dict(
        scheduling_authorization_id=request.scheduling_authorization_id,
        handoff_id=request.handoff_id,
        envelope_id=request.envelope_id,
        claim_id=request.claim_id,
        consumption_id=request.consumption_id,
        authorization_id=request.authorization_id,
        execution_plan_fingerprint=request.execution_plan_fingerprint,
        execution_authorization_decision_fingerprint=request.execution_authorization_decision_fingerprint,
        stage63_claim_fingerprint=request.stage63_claim_fingerprint,
        stage64_envelope_fingerprint=request.stage64_envelope_fingerprint,
        stage65_handoff_receipt_fingerprint=request.stage65_handoff_receipt_fingerprint,
        stage66_scheduling_request_fingerprint=request.stage66_scheduling_request_fingerprint,
        stage66_scheduling_decision_fingerprint=request.stage66_scheduling_decision_fingerprint,
        selected_adapter_index=request.selected_adapter_index,
        runtime_boundary_id=request.runtime_boundary_id,
        runtime_boundary_kind=request.runtime_boundary_kind,
    )
    assert exact_consumption_scope(**values) == request.consumption_scope


def test_consumer_rejects_policy_substitution():
    from core.controlled_runtime_atomic_scheduling_consumption import AtomicSchedulingAuthorizationConsumer
    with pytest.raises(ValueError):
        AtomicSchedulingAuthorizationConsumer(
            policy=AtomicSchedulingAuthorizationConsumptionPolicy(
                complete_chain_layers=22
            )
        )