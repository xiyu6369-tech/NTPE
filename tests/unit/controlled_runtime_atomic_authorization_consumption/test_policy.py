from dataclasses import FrozenInstanceError

import pytest

from core.controlled_runtime_atomic_authorization_consumption import AtomicAuthorizationConsumptionPolicy


def test_policy_is_frozen_and_fail_closed():
    policy = AtomicAuthorizationConsumptionPolicy()
    assert policy.required_unit_count == 1
    assert policy.forbid_execution is True
    with pytest.raises(FrozenInstanceError):
        policy.forbid_execution = False
