from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, replace

import pytest

from core.controlled_runtime_execution_authorization import (
    ControlledRuntimeExecutionAuthorizer,
)
from core.controlled_runtime_execution_authorization.policy import (
    REQUEST_SCHEMA_NAME,
    exact_authorization_scope,
)
from core.controlled_runtime_execution_plan import (
    get_controlled_runtime_preparation_freeze_metadata,
)
from tests.unit.controlled_runtime_execution_authorization import (
    build_plan,
    build_request,
)


def _authorize(plan, request=None, freeze_metadata="default"):
    supplied = (
        get_controlled_runtime_preparation_freeze_metadata()
        if freeze_metadata == "default"
        else freeze_metadata
    )
    return ControlledRuntimeExecutionAuthorizer().authorize(
        request=build_request(plan) if request is None else request,
        execution_plan=plan,
        freeze_metadata=supplied,
    )


def _codes(result) -> set[str]:
    return {finding.code for finding in result.policy_findings}


def _corrupt(value, **changes):
    candidate = copy.copy(value)
    for name, replacement in changes.items():
        object.__setattr__(candidate, name, replacement)
    return candidate


def test_valid_plan_authorizes_without_execution_or_mutation(tmp_path) -> None:
    plan = build_plan(tmp_path)
    request = build_request(plan)
    original = copy.deepcopy((plan, request))
    results = tuple(_authorize(plan, request) for _ in range(3))
    assert results[0] == results[1] == results[2]
    result = results[0]
    assert result.status == "authorized_not_executed"
    assert result.recommended_action == "retain_for_controlled_execution_review"
    assert result.decision.authorized
    assert result.decision.authorized_adapter_index == plan.selected_adapter_unit_indices[0]
    assert result.decision.authorized_unit_count == 1
    assert result.decision.authorized_provider_request_limit == 1
    assert result.decision.authorized_translation_request_limit == 1
    assert result.decision.authorized_retry_limit == 0
    assert result.decision.authorized_fallback_limit == 0
    assert not result.decision.authorization_consumed
    assert not result.decision.authorization_reusable
    assert not any(
        getattr(result.decision, name)
        for name in (
            "output_replacement_authorized",
            "production_integration_authorized",
            "runtime_execution_enabled",
            "provider_execution_enabled",
            "network_execution_enabled",
            "translation_execution_enabled",
        )
    )
    assert not any(
        getattr(result, name)
        for name in (
            "runtime_invoked",
            "provider_invoked",
            "network_invoked",
            "translation_invoked",
            "output_written",
            "resume_written",
            "cache_written",
            "retry_used",
            "fallback_used",
            "production_hook_invoked",
        )
    )
    assert (plan, request) == original
    with pytest.raises(FrozenInstanceError):
        result.status = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.decision.authorized = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.policy_findings[0].message = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"caller_confirmation": False}, "CALLER_CONFIRMATION_REQUIRED"),
        ({"caller_confirmation": 1}, "REQUEST_FIELD_TYPE_INVALID"),
        ({"authorization_id": ""}, "AUTHORIZATION_ID_INVALID"),
        (
            {"authorization_id": "550e8400-e29b-41d4-a716-446655440000"},
            "AUTHORIZATION_ID_INVALID",
        ),
        ({"selected_adapter_index": 999}, "ADAPTER_INDEX_MISMATCH"),
        ({"requested_unit_count": 0}, "MULTIPLE_UNIT_AUTHORIZATION_REJECTED"),
        ({"requested_unit_count": 2}, "MULTIPLE_UNIT_AUTHORIZATION_REJECTED"),
        ({"requested_adapter_indices": (0, 1)}, "MULTIPLE_UNIT_AUTHORIZATION_REJECTED"),
        ({"requested_provider_request_limit": 0}, "PROVIDER_REQUEST_LIMIT_INVALID"),
        ({"requested_provider_request_limit": 2}, "PROVIDER_REQUEST_LIMIT_INVALID"),
        ({"requested_translation_request_limit": 0}, "TRANSLATION_REQUEST_LIMIT_INVALID"),
        ({"requested_translation_request_limit": 2}, "TRANSLATION_REQUEST_LIMIT_INVALID"),
        ({"retry_requested": True}, "RETRY_REQUEST_REJECTED"),
        ({"fallback_requested": True}, "FALLBACK_REQUEST_REJECTED"),
        ({"output_replacement_requested": True}, "OUTPUT_REPLACEMENT_REQUEST_REJECTED"),
        ({"cache_write_requested": True}, "CACHE_WRITE_REQUEST_REJECTED"),
        ({"resume_write_requested": True}, "RESUME_WRITE_REQUEST_REJECTED"),
        ({"production_integration_requested": True}, "PRODUCTION_INTEGRATION_REQUEST_REJECTED"),
        ({"runtime_execution_requested": False}, "RUNTIME_EXECUTION_INTENT_REQUIRED"),
        ({"provider_execution_requested": False}, "PROVIDER_EXECUTION_INTENT_REQUIRED"),
        ({"network_execution_requested": False}, "NETWORK_EXECUTION_INTENT_REQUIRED"),
        ({"translation_execution_requested": False}, "TRANSLATION_EXECUTION_INTENT_REQUIRED"),
        ({"schema_name": "wrong"}, "REQUEST_SCHEMA_MISMATCH"),
        ({"schema_version": "2.0"}, "REQUEST_SCHEMA_MISMATCH"),
        ({"authorization_scope": "all_plans"}, "AUTHORIZATION_SCOPE_MISMATCH"),
        ({"purpose": ""}, "PURPOSE_INVALID"),
        ({"requested_plan_step_fingerprints": ("0" * 64,)}, "PLAN_ORDER_CHANGE_REJECTED"),
    ],
)
def test_invalid_request_fails_closed(tmp_path, changes, code) -> None:
    plan = build_plan(tmp_path)
    result = _authorize(plan, build_request(plan, **changes))
    assert not result.decision.authorized
    assert result.status in {"invalid_request", "rejected"}
    assert code in _codes(result)
    assert not result.decision.runtime_execution_enabled


def test_request_fingerprint_tampering_fails_closed(tmp_path) -> None:
    plan = build_plan(tmp_path)
    request = _corrupt(build_request(plan), purpose="tampered")
    result = _authorize(plan, request)
    assert result.status == "invalid_request"
    assert "REQUEST_FINGERPRINT_MISMATCH" in _codes(result)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("schema_name", "wrong", "EXECUTION_PLAN_SCHEMA_MISMATCH"),
        ("schema_version", "2.0", "EXECUTION_PLAN_SCHEMA_MISMATCH"),
        ("strategy", "wrong", "EXECUTION_PLAN_SCHEMA_MISMATCH"),
        ("activation_gate", "wrong", "EXECUTION_PLAN_SCHEMA_MISMATCH"),
        ("status", "executed", "EXECUTION_PLAN_STATE_INVALID"),
        ("execution_started", True, "EXECUTION_PLAN_ALREADY_STARTED"),
        ("execution_completed", True, "EXECUTION_PLAN_ALREADY_COMPLETED"),
        ("provider_requests_executed", 1, "PROVIDER_EXECUTION_COUNTER_NONZERO"),
        ("translation_executions_completed", 1, "TRANSLATION_EXECUTION_COUNTER_NONZERO"),
        ("runtime_execution_enabled", True, "EXECUTION_PLAN_CAPABILITY_RELAXATION"),
        ("provider_execution_enabled", True, "EXECUTION_PLAN_CAPABILITY_RELAXATION"),
        ("translation_execution_enabled", True, "EXECUTION_PLAN_CAPABILITY_RELAXATION"),
        ("automatic_retry_authorized", True, "EXECUTION_PLAN_CAPABILITY_RELAXATION"),
        ("automatic_fallback_authorized", True, "EXECUTION_PLAN_CAPABILITY_RELAXATION"),
        ("output_replacement_authorized", True, "EXECUTION_PLAN_CAPABILITY_RELAXATION"),
        ("execution_plan_fingerprint", "0" * 64, "EXECUTION_PLAN_FINGERPRINT_MISMATCH"),
    ],
)
def test_plan_tampering_fails_closed(tmp_path, field, value, code) -> None:
    plan = build_plan(tmp_path)
    result = _authorize(_corrupt(plan, **{field: value}), build_request(plan))
    assert not result.decision.authorized
    assert code in _codes(result)


def test_step_text_and_fingerprint_tampering_fail_closed(tmp_path) -> None:
    plan = build_plan(tmp_path)
    for step in (
        _corrupt(plan.steps[0], text=plan.steps[0].text + "tampered"),
        _corrupt(plan.steps[0], execution_step_fingerprint="0" * 64),
    ):
        candidate = _corrupt(plan, steps=(step,))
        result = _authorize(candidate, build_request(plan))
        assert not result.decision.authorized
        assert _codes(result) & {
            "EXECUTION_PLAN_TEXT_FINGERPRINT_MISMATCH",
            "EXECUTION_STEP_FINGERPRINT_MISMATCH",
        }


def test_zero_multiple_and_automatic_plan_scope_fail_closed(tmp_path) -> None:
    plan = build_plan(tmp_path)
    variants = (
        _corrupt(plan, steps=(), selected_adapter_unit_indices=(), planned_step_count=0),
        _corrupt(
            plan,
            steps=(plan.steps[0], plan.steps[0]),
            selected_adapter_unit_indices=(0, 0),
            planned_step_count=2,
        ),
        _corrupt(plan, selected_adapter_unit_indices=()),
    )
    for candidate in variants:
        result = _authorize(candidate, build_request(plan))
        assert not result.decision.authorized
        assert _codes(result) & {
            "EXECUTION_PLAN_SCOPE_INVALID",
            "EXECUTION_PLAN_SELECTION_AUTOMATIC",
            "EXECUTION_PLAN_STATE_INVALID",
        }


def test_freeze_metadata_rejections(tmp_path) -> None:
    plan = build_plan(tmp_path)
    metadata = get_controlled_runtime_preparation_freeze_metadata()
    candidates = (
        None,
        _corrupt(metadata, activation_gate="wrong"),
        _corrupt(metadata, freeze_version="5.3"),
    )
    for candidate in candidates:
        result = _authorize(plan, freeze_metadata=candidate)
        assert result.status == "frozen_contract_mismatch"
        assert not result.freeze_gate_verified
        assert not result.decision.authorized


def test_freeze_validator_failure_is_deterministic(tmp_path) -> None:
    plan = build_plan(tmp_path)

    def fail():
        raise RuntimeError("details must not leak")

    authorizer = ControlledRuntimeExecutionAuthorizer(freeze_validator=fail)
    result = authorizer.authorize(
        request=build_request(plan),
        execution_plan=plan,
        freeze_metadata=get_controlled_runtime_preparation_freeze_metadata(),
    )
    assert result.status == "frozen_contract_mismatch"
    assert "FREEZE_VALIDATION_FAILED" in _codes(result)
    assert "details must not leak" not in result.to_json()


def test_unicode_crlf_and_dictionary_order_are_deterministic(tmp_path) -> None:
    plan = build_plan(tmp_path)
    first = build_request(plan, purpose="授權\r\n目的")
    second = build_request(plan, purpose="授權\r\n目的")
    assert first.request_fingerprint == second.request_fingerprint
    assert first.to_json() == second.to_json()
    assert _authorize(plan, first) == _authorize(plan, second)


def test_policy_relevant_changes_change_request_fingerprint(tmp_path) -> None:
    plan = build_plan(tmp_path)
    original = build_request(plan)
    for field, value in (
        ("authorization_id", "different-caller-id"),
        ("purpose", "不同目的"),
        ("requested_provider_request_limit", 0),
        ("retry_requested", True),
    ):
        assert replace(original, **{field: value}).request_fingerprint != original.request_fingerprint


def test_complete_fingerprint_chain_is_preserved(tmp_path) -> None:
    plan = build_plan(tmp_path)
    result = _authorize(plan)
    decision = result.decision
    assert decision.execution_package_fingerprint == plan.source.execution_package_fingerprint
    assert decision.upstream_authorization_decision_fingerprint == plan.source.authorization_fingerprint
    assert decision.approval_record_fingerprint == plan.source.approval_record_fingerprint
    assert decision.runtime_submission_package_fingerprint == plan.source.runtime_submission_package_fingerprint
    assert decision.runtime_adapter_request_fingerprint == plan.source.runtime_adapter_request_fingerprint
    assert decision.runtime_adapter_preparation_fingerprint == plan.source.runtime_adapter_preparation_fingerprint
    assert decision.authorization_request_fingerprint == result.request.request_fingerprint
    assert decision.authorized_execution_plan_fingerprint == plan.execution_plan_fingerprint

