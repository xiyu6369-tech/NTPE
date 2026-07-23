from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from core.controlled_runtime_adapter import (
    RuntimeAdapterCapabilityProfile,
    RuntimeAdapterFinding,
    RuntimeAdapterPreparationResult,
    RuntimeAdapterRequest,
    RuntimeAdapterSourceReference,
    RuntimeAdapterUnit,
)


HEX = "a" * 64


def _profile() -> RuntimeAdapterCapabilityProfile:
    return RuntimeAdapterCapabilityProfile(
        "ntpe.controlled_runtime_adapter.offline_preparation",
        "1.0",
        True,
        True,
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
    )


def _source() -> RuntimeAdapterSourceReference:
    return RuntimeAdapterSourceReference(
        "novel.txt", HEX, HEX, HEX, HEX, HEX, HEX, HEX, HEX, HEX
    )


def _unit() -> RuntimeAdapterUnit:
    return RuntimeAdapterUnit(
        adapter_unit_index=0,
        submission_index=0,
        execution_unit_index=0,
        execution_unit_id="execution-unit-000000-aaaaaaaaaaaaaaaa",
        text="中文\r\n",
        source_character_start=0,
        source_character_end=4,
        section_indices=(0,),
        heading_text=None,
        boundary_reason="source_end",
        character_count=4,
        non_whitespace_character_count=2,
        source_chunk_fingerprint=HEX,
        execution_unit_fingerprint=HEX,
        runtime_submission_unit_fingerprint=HEX,
        runtime_adapter_unit_fingerprint=HEX,
        status="prepared_for_runtime_adapter",
        runtime_attempt_count=0,
        provider_request_count=0,
        translation_result_attached=False,
    )


def _request() -> RuntimeAdapterRequest:
    return RuntimeAdapterRequest(
        schema_name="ntpe.controlled_runtime_adapter_request",
        schema_version="1.0",
        strategy="deterministic_offline_runtime_adapter_v1",
        activation_gate="controlled_runtime_adapter_prepared",
        source=_source(),
        capability_profile=_profile(),
        units=(_unit(),),
        approved_unit_indices=(0,),
        adapter_unit_count=1,
        original_execution_unit_count=1,
        approved_character_count=4,
        original_character_count=4,
        approval_coverage_ratio=1.0,
        status="prepared_for_runtime_adapter",
        action="hold_for_controlled_runtime_execution_stage",
        findings=(RuntimeAdapterFinding("CODE", "info", "message"),),
        summary="prepared",
        provider_execution_authorized=True,
        translation_execution_authorized=True,
        runtime_submission_authorized=True,
        automatic_retry_authorized=False,
        automatic_fallback_authorized=False,
        output_replacement_authorized=False,
        runtime_submission_executed=False,
        provider_requests_executed=0,
        translation_executions_completed=0,
        runtime_adapter_request_fingerprint=HEX,
    )


def _result() -> RuntimeAdapterPreparationResult:
    request = _request()
    return RuntimeAdapterPreparationResult(
        request=request,
        capability_profile=request.capability_profile,
        prepared=True,
        compatible=True,
        runtime_invoked=False,
        provider_invoked=False,
        translation_invoked=False,
        status=request.status,
        action=request.action,
        findings=request.findings,
        summary="prepared offline",
        preparation_fingerprint=HEX,
    )


def test_all_formal_models_are_frozen_and_collections_are_tuples() -> None:
    result = _result()
    request = result.request
    assert isinstance(request.units, tuple)
    assert isinstance(request.findings, tuple)
    assert isinstance(request.approved_unit_indices, tuple)
    assert isinstance(request.units[0].section_indices, tuple)
    for value in (
        result,
        request,
        request.source,
        request.capability_profile,
        request.units[0],
        request.findings[0],
    ):
        with pytest.raises(FrozenInstanceError):
            value.status = "changed"  # type: ignore[attr-defined]


def test_content_properties_and_serialization_are_deterministic_detached() -> None:
    result = _result()
    request = result.request
    assert request.reconstruct_approved_text() == "中文\r\n"
    assert request.is_full_package_request
    assert not request.is_partial_scope_request
    assert request.to_json() == request.to_json()
    assert result.to_json() == result.to_json()
    assert json.loads(request.to_json()) == request.to_dict()
    assert json.loads(result.to_json()) == result.to_dict()
    assert "中文" in result.to_json()
    detached = result.to_dict()
    detached["request"]["units"][0]["text"] = "changed"  # type: ignore[index]
    assert request.units[0].text == "中文\r\n"


@pytest.mark.parametrize("field", ["units", "findings", "approved_unit_indices"])
def test_request_rejects_mutable_collection_fields(field: str) -> None:
    values = _request().__dict__.copy()
    values[field] = list(values[field])
    with pytest.raises(TypeError):
        RuntimeAdapterRequest(**values)
