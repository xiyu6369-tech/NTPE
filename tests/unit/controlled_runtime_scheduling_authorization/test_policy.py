from dataclasses import FrozenInstanceError

import pytest

from core.controlled_runtime_scheduling_authorization import (
    ControlledRuntimeSchedulingAuthorizationPolicy,
)
from core.controlled_runtime_scheduling_authorization.policy import (
    ALLOWED_RECOMMENDED_ACTIONS,
    ALLOWED_RESULT_STATUSES,
    exact_scheduling_scope,
)


def test_policy_is_frozen_and_exactly_single_use():
    policy = ControlledRuntimeSchedulingAuthorizationPolicy()
    assert policy.authorized_schedule_unit_count == 1
    assert policy.maximum_provider_requests == 1
    assert policy.maximum_translation_requests == 1
    assert policy.maximum_retries == 0
    assert policy.maximum_fallbacks == 0
    assert policy.schedule_once is True
    assert policy.complete_chain_layers == 19
    with pytest.raises(FrozenInstanceError):
        policy.complete_chain_layers = 20


def test_statuses_and_actions_are_bounded():
    assert (
        "scheduling_authorized_not_consumed_not_scheduled"
        in ALLOWED_RESULT_STATUSES
    )
    assert (
        "retain_for_atomic_scheduling_authorization_consumption"
        in ALLOWED_RECOMMENDED_ACTIONS
    )
    assert "schedule" not in ALLOWED_RECOMMENDED_ACTIONS


def test_scope_binds_every_identity_and_one_unit_deterministically():
    kwargs = dict(
        handoff_id="h", envelope_id="e", claim_id="c",
        consumption_id="co", authorization_id="a",
        execution_plan_fingerprint="1" * 64,
        execution_authorization_decision_fingerprint="2" * 64,
        stage63_claim_fingerprint="3" * 64,
        stage64_envelope_fingerprint="4" * 64,
        stage65_handoff_receipt_fingerprint="5" * 64,
        selected_adapter_index=0, runtime_boundary_id="b",
    )
    scope = exact_scheduling_scope(**kwargs)
    assert scope == exact_scheduling_scope(**dict(reversed(tuple(kwargs.items()))))
    for value in ("h", "e", "c", "co", "a", "b"):
        assert value in scope
    assert '"requested_schedule_unit_count":1' in scope
