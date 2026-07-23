from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from core.controlled_runtime_execution_authorization.authorizer import (
    ControlledRuntimeExecutionAuthorizer,
)
from core.controlled_runtime_execution_authorization.errors import (
    InvalidControlledRuntimeExecutionAuthorizationInputError,
)
from core.controlled_runtime_execution_authorization.policy import (
    DEFAULT_POLICY,
    exact_authorization_scope,
)


def test_default_policy_is_immutable_and_fail_closed() -> None:
    with pytest.raises(FrozenInstanceError):
        DEFAULT_POLICY.retry_limit = 1  # type: ignore[misc]
    assert DEFAULT_POLICY.maximum_authorized_units == 1
    assert DEFAULT_POLICY.provider_request_limit == 1
    assert DEFAULT_POLICY.translation_request_limit == 1
    assert DEFAULT_POLICY.retry_limit == 0
    assert DEFAULT_POLICY.fallback_limit == 0
    assert not any(
        getattr(DEFAULT_POLICY, name)
        for name in (
            "output_replacement_authorized",
            "production_integration_authorized",
            "runtime_execution_enabled",
            "provider_execution_enabled",
            "network_execution_enabled",
            "translation_execution_enabled",
            "authorization_reusable",
        )
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("maximum_authorized_units", 2),
        ("provider_request_limit", 2),
        ("translation_request_limit", 2),
        ("retry_limit", 1),
        ("fallback_limit", 1),
        ("output_replacement_authorized", True),
        ("production_integration_authorized", True),
        ("runtime_execution_enabled", True),
        ("provider_execution_enabled", True),
        ("network_execution_enabled", True),
        ("translation_execution_enabled", True),
        ("authorization_reusable", True),
    ],
)
def test_policy_relaxation_is_rejected(field: str, value: object) -> None:
    with pytest.raises(InvalidControlledRuntimeExecutionAuthorizationInputError):
        ControlledRuntimeExecutionAuthorizer(
            replace(DEFAULT_POLICY, **{field: value})
        )


def test_scope_is_exact_and_deterministic() -> None:
    fingerprint = "a" * 64
    assert exact_authorization_scope(fingerprint, 3) == (
        "controlled_runtime_execution_plan:"
        + fingerprint
        + ":adapter_index:3:unit_count:1"
    )

