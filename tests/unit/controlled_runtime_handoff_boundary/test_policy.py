from dataclasses import FrozenInstanceError

import pytest

from core.controlled_runtime_handoff_boundary import ControlledRuntimeHandoffPolicy
from core.controlled_runtime_handoff_boundary.policy import (
    ALLOWED_RECOMMENDED_ACTIONS,
    ALLOWED_RESULT_STATUSES,
    BOUNDARY_KIND,
    exact_handoff_scope,
)


def test_policy_is_immutable_and_exact():
    policy = ControlledRuntimeHandoffPolicy()
    assert policy.boundary_kind == BOUNDARY_KIND
    assert policy.complete_chain_layers == 17
    with pytest.raises(FrozenInstanceError):
        policy.complete_chain_layers = 18


def test_statuses_and_actions_are_bounded():
    assert "handoff_accepted_not_scheduled_not_executed" in ALLOWED_RESULT_STATUSES
    assert "retain_for_controlled_scheduling_authorization" in ALLOWED_RECOMMENDED_ACTIONS
    assert "execute" not in ALLOWED_RECOMMENDED_ACTIONS


def test_scope_binds_every_required_identity_deterministically():
    kwargs = dict(
        envelope_id="e", authorization_id="a", claim_id="c",
        execution_plan_fingerprint="f" * 64, selected_adapter_index=0,
        runtime_boundary_id="b",
    )
    scope = exact_handoff_scope(**kwargs)
    assert scope == exact_handoff_scope(**dict(reversed(tuple(kwargs.items()))))
    for value in ("e", "a", "c", "f" * 64, "b"):
        assert value in scope
    assert '"requested_unit_count":1' in scope
