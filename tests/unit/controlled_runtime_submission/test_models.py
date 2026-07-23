from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from core.controlled_runtime_submission import (
    RuntimeSubmissionFinding,
    RuntimeSubmissionPackage,
    RuntimeSubmissionSourceReference,
    RuntimeSubmissionUnit,
)

HEX = "a" * 64


def _source() -> RuntimeSubmissionSourceReference:
    return RuntimeSubmissionSourceReference(
        source_name="novel.txt",
        source_content_fingerprint=HEX,
        execution_package_fingerprint=HEX,
        authorization_fingerprint=HEX,
        approval_record_fingerprint=HEX,
        manifest_fingerprint=HEX,
        segmentation_fingerprint=HEX,
        chunk_plan_fingerprint=HEX,
        preparation_fingerprint=HEX,
    )


def _unit() -> RuntimeSubmissionUnit:
    return RuntimeSubmissionUnit(
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
        status="queued_for_controlled_submission",
        runtime_attempt_count=0,
        provider_request_count=0,
        translation_result_attached=False,
    )


def _package() -> RuntimeSubmissionPackage:
    unit = _unit()
    finding = RuntimeSubmissionFinding("CODE", "info", "message")
    return RuntimeSubmissionPackage(
        schema_name="ntpe.controlled_runtime_submission_package",
        schema_version="1.0",
        strategy="deterministic_controlled_runtime_submission_v1",
        activation_gate="controlled_runtime_submission_prepared",
        source=_source(), units=(unit,), approved_unit_indices=(0,),
        submission_unit_count=1, original_execution_unit_count=1,
        character_count=4, covered_character_count=4, coverage_ratio=1.0,
        approved_character_count=4, original_character_count=4,
        approval_coverage_ratio=1.0,
        status="prepared_for_controlled_submission", action="hold_for_runtime_adapter",
        findings=(finding,), summary="prepared",
        provider_execution_authorized=True,
        translation_execution_authorized=True,
        runtime_submission_authorized=True,
        automatic_retry_authorized=False,
        automatic_fallback_authorized=False,
        output_replacement_authorized=False,
        runtime_submission_executed=False,
        provider_requests_executed=0,
        translation_executions_completed=0,
        runtime_submission_package_fingerprint=HEX,
    )


def test_formal_models_are_frozen_and_collections_are_tuples() -> None:
    package = _package()
    assert isinstance(package.units, tuple)
    assert isinstance(package.findings, tuple)
    assert isinstance(package.approved_unit_indices, tuple)
    assert isinstance(package.units[0].section_indices, tuple)
    for value in (package, package.source, package.units[0], package.findings[0]):
        with pytest.raises(FrozenInstanceError):
            value.schema_name = "changed"  # type: ignore[attr-defined]


def test_reconstruction_full_detection_and_serialization_are_deterministic() -> None:
    package = _package()
    assert package.reconstruct_approved_text() == "中文\r\n"
    assert package.is_full_package_submission is True
    assert package.to_json() == package.to_json()
    assert json.loads(package.to_json()) == package.to_dict()
    assert "中文" in package.to_json()
    detached = package.to_dict()
    detached["units"][0]["text"] = "changed"  # type: ignore[index]
    assert package.units[0].text == "中文\r\n"


@pytest.mark.parametrize("field", ["units", "findings", "approved_unit_indices"])
def test_package_rejects_mutable_collections(field: str) -> None:
    values = _package().__dict__.copy()
    values[field] = list(values[field])
    with pytest.raises(TypeError):
        RuntimeSubmissionPackage(**values)