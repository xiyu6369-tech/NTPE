from __future__ import annotations

import copy
import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor
from core.controlled_runtime_adapter import ControlledRuntimeAdapter
from core.controlled_runtime_execution_plan import (
    ControlledRuntimeExecutionConsistencyError,
    ControlledRuntimeExecutionPlanner,
    ControlledRuntimeExecutionPolicyError,
    ControlledRuntimeExecutionScopeError,
    InvalidControlledRuntimeExecutionInputError,
)
from core.controlled_runtime_execution_plan.policy import DEFAULT_POLICY
from core.controlled_runtime_submission import ControlledRuntimeSubmissionBuilder
from core.translation_execution_approval import (
    ExplicitHumanApprovalRequest,
    TranslationExecutionApprover,
)
from core.translation_execution_authorization import (
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_package import TranslationExecutionPackageBuilder


def _corrupt(target, **changes):
    candidate = copy.copy(target)
    for name, value in changes.items():
        object.__setattr__(candidate, name, value)
    return candidate


def _adapter_result(
    tmp_path: Path,
    *,
    approval_type: str = "full_package",
    indices: tuple[int, ...] | None = None,
    warning: bool = False,
    adapter_profile=None,
):
    text = (
        "Chapter 1\n"
        + "Sentence. " * 300
        + "\nChapter 2\n"
        + "More sentence. " * 300
        if warning
        else "Chapter 1\n"
        + "Sentence. " * 180
        + "\nChapter 2\n"
        + "Another sentence. " * 110
    )
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))
    package = TranslationExecutionPackageBuilder().build(
        BookPreparationProcessor().prepare(source)
    )
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    indices = tuple(range(package.unit_count)) if indices is None else indices
    statement = "APPROVE_CONTROLLED_TRANSLATION_EXECUTION: planner scope"
    if package.status == "prepared_with_warnings":
        statement += " ACKNOWLEDGE_PACKAGE_WARNINGS"
    approval_request = ExplicitHumanApprovalRequest(
        approval_type=approval_type,
        approved_package_fingerprint=package.execution_package_fingerprint,
        approved_authorization_fingerprint=decision.authorization_fingerprint,
        approved_unit_indices=indices,
        approve_provider_execution=True,
        approve_translation_execution=True,
        approve_runtime_submission=True,
        approve_automatic_retry=False,
        approve_automatic_fallback=False,
        approve_output_replacement=False,
        approval_statement=statement,
        approval_reference="stage53-unit-test",
    )
    record = TranslationExecutionApprover().approve(
        package=package,
        authorization_decision=decision,
        approval_request=approval_request,
    )
    submission = ControlledRuntimeSubmissionBuilder().build(
        package=package,
        authorization_decision=decision,
        approval_record=record,
    )
    result = ControlledRuntimeAdapter(adapter_profile).prepare(
        submission_package=submission
    )
    return result, text


def test_explicit_single_unit_plan_maps_exactly_and_remains_disabled(
    tmp_path: Path,
) -> None:
    result, _ = _adapter_result(tmp_path)
    plan = ControlledRuntimeExecutionPlanner().plan(
        adapter_preparation_result=result,
        selected_adapter_unit_indices=(1,),
    )
    unit = result.request.units[1]
    step = plan.steps[0]
    assert plan.planned_step_count == 1
    assert plan.selected_adapter_unit_indices == (1,)
    assert step.step_index == 0
    assert step.adapter_unit_index == unit.adapter_unit_index
    assert step.submission_index == unit.submission_index
    assert step.execution_unit_index == unit.execution_unit_index
    assert step.execution_unit_id == unit.execution_unit_id
    assert step.text == unit.text
    assert step.source_character_start == unit.source_character_start
    assert step.source_character_end == unit.source_character_end
    assert step.section_indices == unit.section_indices
    assert step.source_chunk_fingerprint == unit.source_chunk_fingerprint
    assert step.execution_unit_fingerprint == unit.execution_unit_fingerprint
    assert (
        step.runtime_submission_unit_fingerprint
        == unit.runtime_submission_unit_fingerprint
    )
    assert (
        step.runtime_adapter_unit_fingerprint
        == unit.runtime_adapter_unit_fingerprint
    )
    assert step.planned_provider_request_limit == 1
    assert step.planned_retry_limit == 0
    assert step.planned_fallback_limit == 0
    assert step.status == "planned_not_executed"
    assert step.runtime_attempt_count == step.provider_request_count == 0
    assert step.translation_result_attached is False
    assert plan.runtime_execution_authorized
    assert plan.provider_execution_authorized
    assert plan.translation_execution_authorized
    assert not plan.runtime_execution_enabled
    assert not plan.provider_execution_enabled
    assert not plan.translation_execution_enabled
    assert not plan.execution_started
    assert not plan.execution_completed
    assert plan.provider_requests_executed == 0
    assert plan.translation_executions_completed == 0
    assert plan.action == "hold_for_explicit_runtime_execution_enablement"
    assert not plan.covers_full_approved_scope


def test_scope_coverage_reconstruction_warning_and_findings(tmp_path: Path) -> None:
    result, _ = _adapter_result(tmp_path)
    plan = ControlledRuntimeExecutionPlanner().plan(
        adapter_preparation_result=result,
        selected_adapter_unit_indices=(0,),
    )
    selected = result.request.units[0]
    assert plan.reconstruct_planned_text() == selected.text
    assert plan.planned_character_count == len(selected.text)
    assert plan.approved_character_count == result.request.approved_character_count
    assert plan.planned_approval_coverage_ratio == (
        len(selected.text) / result.request.approved_character_count
    )
    assert {finding.code for finding in plan.findings} >= {
        "CONTROLLED_RUNTIME_EXECUTION_PLAN_PREPARED",
        "SINGLE_UNIT_EXECUTION_SCOPE",
        "EXPLICIT_RUNTIME_ENABLEMENT_REQUIRED",
        "RUNTIME_EXECUTION_NOT_STARTED",
        "RUNTIME_EXECUTION_NOT_COMPLETED",
        "PROVIDER_REQUEST_COUNT_ZERO",
        "TRANSLATION_EXECUTION_COUNT_ZERO",
        "RUNTIME_EXECUTION_CAPABILITY_DISABLED",
        "PROVIDER_EXECUTION_CAPABILITY_DISABLED",
        "TRANSLATION_EXECUTION_CAPABILITY_DISABLED",
    }
    warning_result, _ = _adapter_result(tmp_path, warning=True)
    warning_plan = ControlledRuntimeExecutionPlanner().plan(
        adapter_preparation_result=warning_result,
        selected_adapter_unit_indices=(0,),
    )
    assert warning_plan.status == "planned_with_warnings"
    assert "ADAPTER_WARNING_PROPAGATED" in {
        finding.code for finding in warning_plan.findings
    }


def test_single_upstream_unit_is_the_only_full_approved_scope_case(
    tmp_path: Path,
) -> None:
    result, _ = _adapter_result(
        tmp_path,
        approval_type="single_unit",
        indices=(0,),
    )
    plan = ControlledRuntimeExecutionPlanner().plan(
        adapter_preparation_result=result,
        selected_adapter_unit_indices=(0,),
    )
    assert plan.covers_full_approved_scope
    assert plan.planned_approval_coverage_ratio == 1.0


@pytest.mark.parametrize(
    ("indices", "code"),
    [
        (None, "EXECUTION_SCOPE_EMPTY"),
        ((), "EXECUTION_SCOPE_EMPTY"),
        ((0, 1), "EXECUTION_SCOPE_MULTIPLE_UNITS_REJECTED"),
        ((True,), "EXECUTION_SCOPE_TYPE_MISMATCH"),
        (("0",), "EXECUTION_SCOPE_TYPE_MISMATCH"),
        ((-1,), "EXECUTION_SCOPE_OUT_OF_RANGE"),
        ((999,), "EXECUTION_SCOPE_OUT_OF_RANGE"),
    ],
)
def test_scope_failures_are_explicit_and_never_auto_select(
    tmp_path: Path,
    indices,
    code: str,
) -> None:
    result, _ = _adapter_result(tmp_path)
    with pytest.raises(ControlledRuntimeExecutionScopeError) as caught:
        ControlledRuntimeExecutionPlanner().plan(
            adapter_preparation_result=result,
            selected_adapter_unit_indices=indices,
        )
    assert caught.value.finding.code == code


def test_selected_unit_must_belong_to_upstream_approved_scope(
    tmp_path: Path,
) -> None:
    result, _ = _adapter_result(tmp_path)
    request = _corrupt(result.request, approved_unit_indices=(1,))
    result = _corrupt(result, request=request)
    with pytest.raises(ControlledRuntimeExecutionScopeError) as caught:
        ControlledRuntimeExecutionPlanner().plan(
            adapter_preparation_result=result,
            selected_adapter_unit_indices=(0,),
        )
    assert caught.value.finding.code == "EXECUTION_SCOPE_NOT_APPROVED"


def test_three_plans_are_identical_non_mutating_and_serializable(
    tmp_path: Path,
) -> None:
    result, _ = _adapter_result(tmp_path)
    original = copy.deepcopy(result)
    plans = tuple(
        ControlledRuntimeExecutionPlanner().plan(
            adapter_preparation_result=result,
            selected_adapter_unit_indices=(0,),
        )
        for _ in range(3)
    )
    assert plans[0] == plans[1] == plans[2]
    assert plans[0].to_json() == plans[1].to_json() == plans[2].to_json()
    assert result == original
    assert re.fullmatch(r"[0-9a-f]{64}", plans[0].execution_plan_fingerprint)
    assert re.fullmatch(
        r"[0-9a-f]{64}",
        plans[0].steps[0].execution_step_fingerprint,
    )
    payload = json.loads(plans[0].to_json())
    assert "approval_statement" not in plans[0].to_json()
    assert "timestamp" not in payload and "uuid" not in payload
    detached = plans[0].to_dict()
    detached["steps"][0]["text"] = "changed"
    assert plans[0].steps[0].text != "changed"
    for method in ("execute", "run", "submit", "translate", "dispatch"):
        assert not hasattr(ControlledRuntimeExecutionPlanner, method)


def test_selected_unit_and_stricter_adapter_profile_change_plan_fingerprint(
    tmp_path: Path,
) -> None:
    result, _ = _adapter_result(tmp_path)
    planner = ControlledRuntimeExecutionPlanner()
    first = planner.plan(
        adapter_preparation_result=result,
        selected_adapter_unit_indices=(0,),
    )
    second = planner.plan(
        adapter_preparation_result=result,
        selected_adapter_unit_indices=(1,),
    )
    assert first.execution_plan_fingerprint != second.execution_plan_fingerprint

    stricter_profile = replace(
        result.capability_profile,
        supports_partial_scope=False,
    )
    stricter_result, _ = _adapter_result(
        tmp_path,
        adapter_profile=stricter_profile,
    )
    stricter = planner.plan(
        adapter_preparation_result=stricter_result,
        selected_adapter_unit_indices=(0,),
    )
    assert stricter.execution_plan_fingerprint != first.execution_plan_fingerprint


def test_zero_request_policy_explicitly_rejects_planning(tmp_path: Path) -> None:
    result, _ = _adapter_result(tmp_path)
    policy = replace(
        DEFAULT_POLICY,
        maximum_provider_requests_per_unit=0,
        maximum_total_provider_requests=0,
    )
    with pytest.raises(ControlledRuntimeExecutionPolicyError):
        ControlledRuntimeExecutionPlanner(policy).plan(
            adapter_preparation_result=result,
            selected_adapter_unit_indices=(0,),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("prepared", False),
        ("compatible", False),
        ("runtime_invoked", True),
        ("provider_invoked", True),
        ("translation_invoked", True),
        ("preparation_fingerprint", "0" * 64),
        ("status", "completed"),
        ("action", "execute"),
    ],
)
def test_adapter_preparation_tampering_fails_closed(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    result, _ = _adapter_result(tmp_path)
    result = _corrupt(result, **{field: value})
    with pytest.raises(ControlledRuntimeExecutionConsistencyError):
        ControlledRuntimeExecutionPlanner().plan(
            adapter_preparation_result=result,
            selected_adapter_unit_indices=(0,),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_name", "wrong"),
        ("schema_version", "2.0"),
        ("strategy", "wrong"),
        ("activation_gate", "wrong"),
        ("runtime_adapter_request_fingerprint", "0" * 64),
        ("provider_execution_authorized", False),
        ("translation_execution_authorized", False),
        ("runtime_submission_authorized", False),
        ("automatic_retry_authorized", True),
        ("provider_requests_executed", 1),
        ("translation_executions_completed", 1),
        ("approved_character_count", 1),
    ],
)
def test_adapter_request_tampering_fails_closed(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    result, _ = _adapter_result(tmp_path)
    result = _corrupt(result, request=_corrupt(result.request, **{field: value}))
    with pytest.raises(ControlledRuntimeExecutionConsistencyError):
        ControlledRuntimeExecutionPlanner().plan(
            adapter_preparation_result=result,
            selected_adapter_unit_indices=(0,),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("runtime_adapter_unit_fingerprint", "0" * 64),
        ("text", "tampered"),
        ("source_character_start", -1),
        ("status", "executed"),
        ("runtime_attempt_count", 1),
        ("provider_request_count", 1),
        ("translation_result_attached", True),
    ],
)
def test_adapter_unit_tampering_fails_closed(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    result, _ = _adapter_result(tmp_path)
    units = list(result.request.units)
    units[0] = _corrupt(units[0], **{field: value})
    request = _corrupt(result.request, units=tuple(units))
    result = _corrupt(result, request=request)
    with pytest.raises(ControlledRuntimeExecutionConsistencyError):
        ControlledRuntimeExecutionPlanner().plan(
            adapter_preparation_result=result,
            selected_adapter_unit_indices=(0,),
        )


def test_capability_and_findings_tampering_fails_closed(tmp_path: Path) -> None:
    result, _ = _adapter_result(tmp_path)
    profile = _corrupt(result.capability_profile, supports_provider_execution=True)
    variants = (
        _corrupt(result, capability_profile=profile),
        _corrupt(result, request=_corrupt(result.request, findings=())),
    )
    for candidate in variants:
        with pytest.raises(ControlledRuntimeExecutionConsistencyError):
            ControlledRuntimeExecutionPlanner().plan(
                adapter_preparation_result=candidate,
                selected_adapter_unit_indices=(0,),
            )


def test_invalid_input_type_is_distinct() -> None:
    with pytest.raises(InvalidControlledRuntimeExecutionInputError):
        ControlledRuntimeExecutionPlanner().plan(
            adapter_preparation_result="invalid",  # type: ignore[arg-type]
            selected_adapter_unit_indices=(0,),
        )
