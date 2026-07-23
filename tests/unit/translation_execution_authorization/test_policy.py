from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from types import MappingProxyType

import pytest

from core.translation_execution_authorization import (
    ExecutionAuthorizationPolicyError,
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_authorization.policy import (
    ALLOW_FLAG_NAMES,
    DEFAULT_POLICY,
    EXECUTION_FLAG_NAMES,
    FINDING_CODES,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
)


def test_default_policy_is_immutable_and_fail_closed() -> None:
    assert DEFAULT_POLICY.policy_name == "ntpe.translation_execution_authorization"
    assert DEFAULT_POLICY.policy_version == "1.0"
    assert all(getattr(DEFAULT_POLICY, name) is False for name in ALLOW_FLAG_NAMES)
    assert all(getattr(DEFAULT_POLICY, name) is False for name in EXECUTION_FLAG_NAMES)
    assert DEFAULT_POLICY.require_explicit_human_approval is True
    assert not any(
        isinstance(value, (list, dict, set))
        for value in DEFAULT_POLICY.__dict__.values()
    )
    with pytest.raises(FrozenInstanceError):
        DEFAULT_POLICY.allow_prepared = True


def test_finding_policy_is_immutable_complete_and_ordered() -> None:
    assert isinstance(FINDING_SEVERITIES, MappingProxyType)
    assert isinstance(FINDING_MESSAGES, MappingProxyType)
    assert isinstance(FINDING_ORDER, MappingProxyType)
    assert set(FINDING_CODES) == set(FINDING_SEVERITIES) == set(FINDING_MESSAGES)
    assert tuple(sorted(FINDING_CODES, key=FINDING_ORDER.__getitem__)) == FINDING_CODES
    with pytest.raises(TypeError):
        FINDING_MESSAGES["EXPLICIT_AUTHORIZATION_REQUIRED"] = "changed"


@pytest.mark.parametrize("field", [*ALLOW_FLAG_NAMES, *EXECUTION_FLAG_NAMES])
def test_policy_relaxation_flags_are_rejected(field: str) -> None:
    with pytest.raises(ExecutionAuthorizationPolicyError) as captured:
        TranslationExecutionAuthorizationEvaluator(
            replace(DEFAULT_POLICY, **{field: True})
        )
    assert captured.value.finding.code == "POLICY_RELAXATION_REJECTED"


def test_human_approval_and_required_contract_cannot_be_relaxed() -> None:
    candidates = (
        replace(DEFAULT_POLICY, require_explicit_human_approval=False),
        replace(DEFAULT_POLICY, required_package_schema_name="other"),
        replace(DEFAULT_POLICY, required_package_schema_version="2.0"),
        replace(DEFAULT_POLICY, required_package_activation_gate="other"),
    )
    for policy in candidates:
        with pytest.raises(ExecutionAuthorizationPolicyError):
            TranslationExecutionAuthorizationEvaluator(policy)


def test_equally_strict_versioned_policy_is_accepted() -> None:
    policy = replace(DEFAULT_POLICY, policy_version="1.1-stricter")
    assert TranslationExecutionAuthorizationEvaluator(policy)._policy == policy

