from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from types import MappingProxyType

import pytest

from core.controlled_runtime_adapter import (
    ControlledRuntimeAdapter,
    RuntimeAdapterCapabilityError,
)
from core.controlled_runtime_adapter.policy import (
    ACTIVATION_GATE,
    DEFAULT_CAPABILITY_PROFILE,
    FINDING_CODES,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
    PROFILE_NAME,
    PROFILE_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STATUS_ACTIONS,
    STRATEGY,
)


def test_adapter_schema_and_profile_contract_is_fixed() -> None:
    assert (SCHEMA_NAME, SCHEMA_VERSION) == (
        "ntpe.controlled_runtime_adapter_request",
        "1.0",
    )
    assert STRATEGY == "deterministic_offline_runtime_adapter_v1"
    assert ACTIVATION_GATE == "controlled_runtime_adapter_prepared"
    assert (PROFILE_NAME, PROFILE_VERSION) == (
        "ntpe.controlled_runtime_adapter.offline_preparation",
        "1.0",
    )


def test_default_capability_is_offline_and_frozen() -> None:
    profile = DEFAULT_CAPABILITY_PROFILE
    assert profile.supports_controlled_submission
    assert profile.supports_partial_scope
    assert profile.supports_full_package_scope
    assert not profile.supports_provider_execution
    assert not profile.supports_translation_execution
    assert not profile.supports_automatic_retry
    assert not profile.supports_automatic_fallback
    assert not profile.supports_output_replacement
    assert not profile.supports_resume_write
    assert not profile.supports_cache_write
    assert not profile.supports_output_write
    assert not profile.supports_production_hook
    with pytest.raises(FrozenInstanceError):
        profile.supports_provider_execution = True  # type: ignore[misc]


@pytest.mark.parametrize(
    "field",
    [
        "supports_provider_execution",
        "supports_translation_execution",
        "supports_automatic_retry",
        "supports_automatic_fallback",
        "supports_output_replacement",
        "supports_resume_write",
        "supports_cache_write",
        "supports_output_write",
        "supports_production_hook",
    ],
)
def test_capability_relaxation_is_rejected(field: str) -> None:
    profile = replace(DEFAULT_CAPABILITY_PROFILE, **{field: True})
    with pytest.raises(RuntimeAdapterCapabilityError):
        ControlledRuntimeAdapter(profile)


def test_stricter_profile_is_accepted_at_construction() -> None:
    profile = replace(
        DEFAULT_CAPABILITY_PROFILE,
        supports_partial_scope=False,
    )
    assert ControlledRuntimeAdapter(profile) is not None


def test_policy_mappings_are_immutable_complete_and_ordered() -> None:
    for mapping in (
        FINDING_MESSAGES,
        FINDING_SEVERITIES,
        FINDING_ORDER,
        STATUS_ACTIONS,
    ):
        assert isinstance(mapping, MappingProxyType)
        with pytest.raises(TypeError):
            mapping["NEW"] = "invalid"  # type: ignore[index]
    assert tuple(FINDING_ORDER) == FINDING_CODES
