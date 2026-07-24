"""Tests for Stage 6.4 policy values."""

import pytest

from core.controlled_runtime_execution_envelope.policy import (
    DEFAULT_POLICY,
    ControlledRuntimeExecutionEnvelopePolicy,
    SUCCESS_STATUS,
    SUCCESS_ACTION,
    FROZEN_ACTIVATION_GATE,
    ALLOWED_EXECUTION_MODES,
    ALLOWED_ENVELOPE_STATES,
)


def test_default_policy_is_policy_instance():
    assert isinstance(DEFAULT_POLICY, ControlledRuntimeExecutionEnvelopePolicy)


def test_default_policy_success_status():
    assert SUCCESS_STATUS == "runtime_handoff_prepared_not_executed"


def test_default_policy_success_action():
    assert SUCCESS_ACTION == "retain_for_controlled_runtime_handoff"


def test_default_policy_frozen_gate():
    assert FROZEN_ACTIVATION_GATE == "controlled_runtime_preparation_frozen"


def test_default_policy_min_upstream_chain_layers():
    assert DEFAULT_POLICY.min_upstream_chain_layers == 14


def test_default_policy_complete_chain_layers():
    assert DEFAULT_POLICY.complete_chain_layers == 15


def test_policy_is_frozen():
    p = DEFAULT_POLICY
    assert isinstance(p, ControlledRuntimeExecutionEnvelopePolicy)
    # Frozen dataclass - attempt mutation should fail
    with pytest.raises(Exception):
        p.min_upstream_chain_layers = 10  # type: ignore[attr-defined]


def test_allowed_execution_modes():
    assert "controlled_single_execution" in ALLOWED_EXECUTION_MODES


def test_allowed_envelope_states():
    assert "runtime_handoff_prepared_not_executed" in ALLOWED_ENVELOPE_STATES