from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from core.translation_execution_package.policy import (
    ACTIVATION_GATE,
    AUTHORIZATION_FLAGS,
    DEFAULT_POLICY,
    FINDING_CODES,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
    REQUIRED_ACTIVATION_GATES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STATUS_ACTIONS,
    STRATEGY,
    UNIT_ATTEMPT_COUNT,
    UNIT_PROVIDER_REQUEST_COUNT,
    UNIT_STATUS,
    UNIT_TRANSLATION_RESULT_ATTACHED,
    make_unit_id,
)


def test_schema_strategy_activation_and_required_frozen_gates_are_fixed() -> None:
    assert SCHEMA_NAME == "ntpe.translation_execution_package"
    assert SCHEMA_VERSION == "1.0"
    assert STRATEGY == "deterministic_offline_execution_package_v1"
    assert ACTIVATION_GATE == "translation_execution_package_prepared"
    assert REQUIRED_ACTIVATION_GATES == (
        "book_intake_layer_frozen",
        "book_preparation_pipeline_frozen",
    )


def test_authorization_and_initial_unit_state_are_fail_closed() -> None:
    assert set(AUTHORIZATION_FLAGS.values()) == {False}
    assert UNIT_STATUS == "prepared"
    assert UNIT_ATTEMPT_COUNT == 0
    assert UNIT_PROVIDER_REQUEST_COUNT == 0
    assert UNIT_TRANSLATION_RESULT_ATTACHED is False
    assert STATUS_ACTIONS == {
        "prepared": "hold_for_execution_authorization",
        "prepared_with_warnings": "hold_for_execution_authorization",
        "blocked": "reject",
    }


def test_policy_findings_and_mappings_are_immutable_and_ordered() -> None:
    assert isinstance(AUTHORIZATION_FLAGS, MappingProxyType)
    assert isinstance(FINDING_SEVERITIES, MappingProxyType)
    assert isinstance(FINDING_MESSAGES, MappingProxyType)
    assert isinstance(FINDING_ORDER, MappingProxyType)
    assert tuple(sorted(FINDING_CODES, key=FINDING_ORDER.__getitem__)) == FINDING_CODES
    assert set(FINDING_CODES) == set(FINDING_SEVERITIES) == set(FINDING_MESSAGES)
    with pytest.raises(TypeError):
        AUTHORIZATION_FLAGS["provider_execution_authorized"] = True
    with pytest.raises(FrozenInstanceError):
        DEFAULT_POLICY.strategy = "changed"


def test_unit_id_policy_is_deterministic_unique_and_path_free() -> None:
    fingerprint = "a" * 64
    assert make_unit_id(0, fingerprint) == "unit-000001-aaaaaaaaaaaa"
    assert make_unit_id(0, fingerprint) == make_unit_id(0, fingerprint)
    assert make_unit_id(0, fingerprint) != make_unit_id(1, fingerprint)
    assert "/" not in make_unit_id(0, fingerprint)
    assert "\\" not in make_unit_id(0, fingerprint)

