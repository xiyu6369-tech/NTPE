from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from types import MappingProxyType

import pytest

from core.controlled_runtime_execution_plan import (
    ControlledRuntimeExecutionPlanner,
    ControlledRuntimeExecutionPolicyError,
)
from core.controlled_runtime_execution_plan.policy import (
    ACTIVATION_GATE,
    DEFAULT_POLICY,
    EXECUTION_MODE,
    FINDING_CODES,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
    POLICY_NAME,
    POLICY_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STRATEGY,
)


def test_schema_and_default_policy_are_fixed_and_frozen() -> None:
    assert (SCHEMA_NAME, SCHEMA_VERSION) == (
        "ntpe.controlled_runtime_execution_plan",
        "1.0",
    )
    assert STRATEGY == "deterministic_single_unit_execution_plan_v1"
    assert ACTIVATION_GATE == "controlled_runtime_execution_plan_prepared"
    policy = DEFAULT_POLICY
    assert (policy.policy_name, policy.policy_version) == (
        POLICY_NAME,
        POLICY_VERSION,
    )
    assert policy.execution_mode == EXECUTION_MODE
    assert policy.maximum_units_per_execution == 1
    assert policy.maximum_provider_requests_per_unit == 1
    assert policy.maximum_total_provider_requests == 1
    assert policy.allow_partial_scope
    assert not policy.allow_full_package_scope
    assert not policy.allow_parallel_execution
    assert not policy.allow_automatic_retry
    assert not policy.allow_automatic_fallback
    assert not policy.allow_output_replacement
    assert not policy.allow_output_write
    assert not policy.allow_resume_write
    assert not policy.allow_cache_write
    assert not policy.allow_production_hook
    assert not policy.runtime_execution_enabled
    assert not policy.provider_execution_enabled
    assert not policy.translation_execution_enabled
    with pytest.raises(FrozenInstanceError):
        policy.maximum_units_per_execution = 2  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("maximum_units_per_execution", 2),
        ("maximum_provider_requests_per_unit", 2),
        ("maximum_total_provider_requests", 2),
        ("allow_full_package_scope", True),
        ("allow_parallel_execution", True),
        ("allow_automatic_retry", True),
        ("allow_automatic_fallback", True),
        ("allow_output_replacement", True),
        ("allow_output_write", True),
        ("allow_resume_write", True),
        ("allow_cache_write", True),
        ("allow_production_hook", True),
        ("runtime_execution_enabled", True),
        ("provider_execution_enabled", True),
        ("translation_execution_enabled", True),
    ],
)
def test_policy_relaxation_is_rejected(field: str, value: object) -> None:
    with pytest.raises(ControlledRuntimeExecutionPolicyError):
        ControlledRuntimeExecutionPlanner(
            replace(DEFAULT_POLICY, **{field: value})
        )


def test_stricter_zero_request_policy_is_accepted_at_construction() -> None:
    policy = replace(
        DEFAULT_POLICY,
        maximum_provider_requests_per_unit=0,
        maximum_total_provider_requests=0,
    )
    assert ControlledRuntimeExecutionPlanner(policy) is not None


def test_finding_policy_is_immutable_complete_and_ordered() -> None:
    for mapping in (FINDING_MESSAGES, FINDING_SEVERITIES, FINDING_ORDER):
        assert isinstance(mapping, MappingProxyType)
        with pytest.raises(TypeError):
            mapping["NEW"] = "invalid"  # type: ignore[index]
    assert tuple(FINDING_ORDER) == FINDING_CODES
