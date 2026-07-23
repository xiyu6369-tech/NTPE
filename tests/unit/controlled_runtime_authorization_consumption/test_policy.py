"""Stage 6.2 unit tests — policy."""

from __future__ import annotations

import pytest

from core.controlled_runtime_authorization_consumption.policy import (
    DEFAULT_POLICY,
    ControlledRuntimeAuthorizationConsumptionPolicy,
    exact_consumption_scope,
)


# ---------------------------------------------------------------------------
# Policy is frozen
# ---------------------------------------------------------------------------


def test_policy_frozen() -> None:
    with pytest.raises(Exception):
        DEFAULT_POLICY.require_single_unit = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Default policy invariants
# ---------------------------------------------------------------------------


def test_default_policy_invariants() -> None:
    assert DEFAULT_POLICY.require_single_unit is True
    assert DEFAULT_POLICY.require_unit_count_exactly_one is True
    assert DEFAULT_POLICY.require_caller_confirmation is True
    assert DEFAULT_POLICY.require_explicit_scope is True
    assert DEFAULT_POLICY.forbid_execution is True
    assert DEFAULT_POLICY.forbid_durable_registry_claim is True
    assert DEFAULT_POLICY.forbid_durable_reuse_prevention_claim is True
    assert DEFAULT_POLICY.forbid_enablement is True
    assert DEFAULT_POLICY.forbid_writes is True


# ---------------------------------------------------------------------------
# Policy cannot be created with relaxed enforcement
# ---------------------------------------------------------------------------


def test_policy_cannot_relax_unit_count() -> None:
    with pytest.raises(ValueError):
        ControlledRuntimeAuthorizationConsumptionPolicy(require_unit_count_exactly_one=False)


def test_policy_cannot_relax_forbid_execution() -> None:
    with pytest.raises(ValueError):
        ControlledRuntimeAuthorizationConsumptionPolicy(forbid_execution=False)


def test_policy_cannot_relax_durable_registry() -> None:
    with pytest.raises(ValueError):
        ControlledRuntimeAuthorizationConsumptionPolicy(forbid_durable_registry_claim=False)


def test_policy_cannot_relax_durable_reuse_prevention() -> None:
    with pytest.raises(ValueError):
        ControlledRuntimeAuthorizationConsumptionPolicy(forbid_durable_reuse_prevention_claim=False)


def test_policy_cannot_relax_forbid_enablement() -> None:
    with pytest.raises(ValueError):
        ControlledRuntimeAuthorizationConsumptionPolicy(forbid_enablement=False)


def test_policy_cannot_relax_forbid_writes() -> None:
    with pytest.raises(ValueError):
        ControlledRuntimeAuthorizationConsumptionPolicy(forbid_writes=False)


# ---------------------------------------------------------------------------
# Scope builder
# ---------------------------------------------------------------------------


def test_scope_binding() -> None:
    scope = exact_consumption_scope(
        authorization_id="auth-id",
        authorization_request_fingerprint="a" * 64,
        authorization_decision_fingerprint="b" * 64,
        execution_plan_fingerprint="c" * 64,
        selected_adapter_index=0,
        unit_count=1,
    )
    assert "auth-id" in scope
    assert "a" * 64 in scope
    assert "b" * 64 in scope
    assert "c" * 64 in scope
    assert "index=0" in scope
    assert "units=1" in scope


def test_scope_blank_id_rejected() -> None:
    with pytest.raises(ValueError):
        exact_consumption_scope("", "a" * 64, "b" * 64, "c" * 64, 0, 1)


def test_scope_bool_index_rejected() -> None:
    with pytest.raises(TypeError):
        exact_consumption_scope("auth", "a" * 64, "b" * 64, "c" * 64, True, 1)


def test_scope_bool_unit_rejected() -> None:
    with pytest.raises(TypeError):
        exact_consumption_scope("auth", "a" * 64, "b" * 64, "c" * 64, 0, True)


def test_scope_deterministic() -> None:
    s1 = exact_consumption_scope("auth", "a" * 64, "b" * 64, "c" * 64, 0, 1)
    s2 = exact_consumption_scope("auth", "a" * 64, "b" * 64, "c" * 64, 0, 1)
    assert s1 == s2


def test_scope_differs_on_id() -> None:
    s1 = exact_consumption_scope("auth1", "a" * 64, "b" * 64, "c" * 64, 0, 1)
    s2 = exact_consumption_scope("auth2", "a" * 64, "b" * 64, "c" * 64, 0, 1)
    assert s1 != s2


def test_scope_differs_on_fingerprint() -> None:
    s1 = exact_consumption_scope("auth", "a" * 64, "b" * 64, "c" * 64, 0, 1)
    s2 = exact_consumption_scope("auth", "x" * 64, "b" * 64, "c" * 64, 0, 1)
    assert s1 != s2