from __future__ import annotations

from types import MappingProxyType

import pytest

from core.translation_execution_approval.policy import (
    ACTIVATION_GATE,
    APPROVAL_TYPES,
    CONFIRMATION_TOKEN,
    FINDING_CODES,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
    PROHIBITED_REQUEST_FLAGS,
    REQUIRED_REQUEST_FLAGS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STRATEGY,
    WARNING_ACKNOWLEDGEMENT_TOKEN,
)


def test_frozen_approval_contract_constants() -> None:
    assert SCHEMA_NAME == "ntpe.translation_execution_approval_record"
    assert SCHEMA_VERSION == "1.0"
    assert STRATEGY == "explicit_human_scoped_execution_approval_v1"
    assert ACTIVATION_GATE == "translation_execution_explicitly_approved"
    assert APPROVAL_TYPES == ("single_unit", "selected_units", "full_package")
    assert CONFIRMATION_TOKEN == "APPROVE_CONTROLLED_TRANSLATION_EXECUTION"
    assert WARNING_ACKNOWLEDGEMENT_TOKEN == "ACKNOWLEDGE_PACKAGE_WARNINGS"
    assert REQUIRED_REQUEST_FLAGS == (
        "approve_provider_execution",
        "approve_translation_execution",
        "approve_runtime_submission",
    )
    assert PROHIBITED_REQUEST_FLAGS == (
        "approve_automatic_retry",
        "approve_automatic_fallback",
        "approve_output_replacement",
    )


def test_finding_policy_is_complete_immutable_and_ordered() -> None:
    assert isinstance(FINDING_MESSAGES, MappingProxyType)
    assert isinstance(FINDING_SEVERITIES, MappingProxyType)
    assert isinstance(FINDING_ORDER, MappingProxyType)
    assert set(FINDING_CODES) == set(FINDING_MESSAGES) == set(FINDING_SEVERITIES)
    assert tuple(sorted(FINDING_CODES, key=FINDING_ORDER.__getitem__)) == FINDING_CODES
    with pytest.raises(TypeError):
        FINDING_MESSAGES["EXPLICIT_HUMAN_APPROVAL_CONFIRMED"] = "changed"
