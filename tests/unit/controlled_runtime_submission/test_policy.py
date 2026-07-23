from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from core.controlled_runtime_submission.policy import (
    ACTIVATION_GATE,
    CONTROLLED_AUTHORIZATION_FLAGS,
    DEFAULT_POLICY,
    EXECUTION_STATE,
    FINDING_CODES,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
    PACKAGE_STATUS,
    PACKAGE_WARNING_STATUS,
    PROHIBITED_AUTHORIZATION_FLAGS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STATUS_ACTIONS,
    STRATEGY,
    UNIT_STATUS,
)


def test_schema_strategy_gate_and_initial_states_are_fixed() -> None:
    assert (SCHEMA_NAME, SCHEMA_VERSION) == (
        "ntpe.controlled_runtime_submission_package", "1.0"
    )
    assert STRATEGY == "deterministic_controlled_runtime_submission_v1"
    assert ACTIVATION_GATE == "controlled_runtime_submission_prepared"
    assert UNIT_STATUS == "queued_for_controlled_submission"
    assert DEFAULT_POLICY.unit_runtime_attempt_count == 0
    assert DEFAULT_POLICY.unit_provider_request_count == 0
    assert DEFAULT_POLICY.unit_translation_result_attached is False


def test_authorization_and_execution_boundary_is_fixed() -> None:
    assert dict(CONTROLLED_AUTHORIZATION_FLAGS) == {
        "provider_execution_authorized": True,
        "translation_execution_authorized": True,
        "runtime_submission_authorized": True,
    }
    assert not any(PROHIBITED_AUTHORIZATION_FLAGS.values())
    assert dict(EXECUTION_STATE) == {
        "runtime_submission_executed": False,
        "provider_requests_executed": 0,
        "translation_executions_completed": 0,
    }


def test_finding_policy_and_status_actions_are_immutable_and_ordered() -> None:
    for value in (FINDING_MESSAGES, FINDING_SEVERITIES, FINDING_ORDER, STATUS_ACTIONS):
        assert isinstance(value, MappingProxyType)
        with pytest.raises(TypeError):
            value["NEW"] = "invalid"  # type: ignore[index]
    assert tuple(FINDING_ORDER) == FINDING_CODES
    assert STATUS_ACTIONS[PACKAGE_STATUS] == "hold_for_runtime_adapter"
    assert STATUS_ACTIONS[PACKAGE_WARNING_STATUS] == "hold_for_runtime_adapter"
    with pytest.raises(FrozenInstanceError):
        DEFAULT_POLICY.strategy = "relaxed"  # type: ignore[misc]