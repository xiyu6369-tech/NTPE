from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from core.controlled_runtime_execution_plan import (
    ControlledRuntimeExecutionFinding,
    ControlledRuntimeExecutionPlan,
    ControlledRuntimeExecutionPolicy,
    ControlledRuntimeExecutionSourceReference,
    ControlledRuntimeExecutionStep,
)


HEX = "a" * 64


def _policy() -> ControlledRuntimeExecutionPolicy:
    return ControlledRuntimeExecutionPolicy(
        "ntpe.controlled_runtime_execution_plan",
        "1.0",
        "single_pass_sequential_controlled",
        1,
        1,
        1,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    )


def _source() -> ControlledRuntimeExecutionSourceReference:
    return ControlledRuntimeExecutionSourceReference(
        "novel.txt", HEX, HEX, HEX, HEX, HEX, HEX, HEX, HEX, HEX, HEX, HEX
    )


def _step() -> ControlledRuntimeExecutionStep:
    return ControlledRuntimeExecutionStep(
        step_index=0,
        adapter_unit_index=0,
        submission_index=0,
        execution_unit_index=0,
        execution_unit_id="execution-unit-000000-aaaaaaaaaaaaaaaa",
        text="中文\r\n",
        source_character_start=0,
        source_character_end=4,
        section_indices=(0,),
        source_chunk_fingerprint=HEX,
        execution_unit_fingerprint=HEX,
        runtime_submission_unit_fingerprint=HEX,
        runtime_adapter_unit_fingerprint=HEX,
        planned_provider_request_limit=1,
        planned_retry_limit=0,
        planned_fallback_limit=0,
        status="planned_not_executed",
        runtime_attempt_count=0,
        provider_request_count=0,
        translation_result_attached=False,
        execution_step_fingerprint=HEX,
    )


def _plan() -> ControlledRuntimeExecutionPlan:
    return ControlledRuntimeExecutionPlan(
        schema_name="ntpe.controlled_runtime_execution_plan",
        schema_version="1.0",
        strategy="deterministic_single_unit_execution_plan_v1",
        activation_gate="controlled_runtime_execution_plan_prepared",
        source=_source(),
        policy=_policy(),
        steps=(_step(),),
        selected_adapter_unit_indices=(0,),
        planned_step_count=1,
        available_adapter_unit_count=1,
        planned_character_count=4,
        approved_character_count=4,
        planned_approval_coverage_ratio=1.0,
        status="planned",
        action="hold_for_explicit_runtime_execution_enablement",
        findings=(ControlledRuntimeExecutionFinding("CODE", "info", "message"),),
        summary="planned",
        runtime_execution_authorized=True,
        provider_execution_authorized=True,
        translation_execution_authorized=True,
        runtime_execution_enabled=False,
        provider_execution_enabled=False,
        translation_execution_enabled=False,
        automatic_retry_authorized=False,
        automatic_fallback_authorized=False,
        output_replacement_authorized=False,
        execution_started=False,
        execution_completed=False,
        provider_requests_executed=0,
        translation_executions_completed=0,
        execution_plan_fingerprint=HEX,
    )


def test_all_models_are_frozen_and_collections_are_tuples() -> None:
    plan = _plan()
    assert isinstance(plan.steps, tuple)
    assert isinstance(plan.findings, tuple)
    assert isinstance(plan.selected_adapter_unit_indices, tuple)
    assert isinstance(plan.steps[0].section_indices, tuple)
    for value in (
        plan,
        plan.policy,
        plan.source,
        plan.steps[0],
        plan.findings[0],
    ):
        with pytest.raises(FrozenInstanceError):
            value.status = "changed"  # type: ignore[attr-defined]


def test_plan_properties_and_serialization_are_deterministic_detached() -> None:
    plan = _plan()
    assert plan.is_single_unit_plan
    assert plan.covers_full_approved_scope
    assert plan.reconstruct_planned_text() == "中文\r\n"
    assert plan.to_json() == plan.to_json()
    assert json.loads(plan.to_json()) == plan.to_dict()
    assert "中文" in plan.to_json()
    detached = plan.to_dict()
    detached["steps"][0]["text"] = "changed"  # type: ignore[index]
    assert plan.steps[0].text == "中文\r\n"


@pytest.mark.parametrize(
    "field",
    ["steps", "findings", "selected_adapter_unit_indices"],
)
def test_plan_rejects_mutable_collection_fields(field: str) -> None:
    values = _plan().__dict__.copy()
    values[field] = list(values[field])
    with pytest.raises(TypeError):
        ControlledRuntimeExecutionPlan(**values)
