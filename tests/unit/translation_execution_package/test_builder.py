from __future__ import annotations

import copy
import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from core.book_preparation import (
    BookPreparationFinding,
    BookPreparationProcessor,
)
from core.translation_execution_package import (
    ExecutionPackageConsistencyError,
    InvalidExecutionPackageInputError,
    InvalidPreparationStateError,
    TranslationExecutionPackageBuilder,
)
from core.translation_execution_package.builder import _preparation_fingerprint


def _ready_preparation(tmp_path: Path, text: str | None = None):
    source = text or (
        "Chapter 1\n"
        + "Sentence. " * 180
        + "\nChapter 2\n"
        + "Another sentence. " * 110
    )
    path = tmp_path / "book.txt"
    path.write_bytes(source.encode("utf-8"))
    result = BookPreparationProcessor().prepare(path)
    assert result.status in ({"ready", "ready_with_warnings"} if text is not None else {"ready"})
    return result


def _with_state(preparation, status: str, findings=()):
    actions = {
        "ready": "proceed",
        "ready_with_warnings": "proceed_with_warning",
        "manual_review": "manual_review",
        "blocked": "reject",
    }
    candidate = replace(
        preparation, status=status, action=actions.get(status, "reject"), findings=findings
    )
    return replace(
        candidate, preparation_fingerprint=_preparation_fingerprint(candidate)
    )


def _corrupt(target, **changes):
    candidate = copy.copy(target)
    for name, value in changes.items():
        object.__setattr__(candidate, name, value)
    return candidate


def test_ready_build_maps_every_chunk_one_to_one_without_mutation(tmp_path: Path) -> None:
    preparation = _ready_preparation(tmp_path)
    package = TranslationExecutionPackageBuilder().build(preparation)

    assert package.status == "prepared"
    assert package.action == "hold_for_execution_authorization"
    assert package.unit_count == preparation.chunk_plan.chunk_count
    assert package.reconstruct_source_text() == preparation.reconstruct_text()
    assert package.character_count == len(preparation.reconstruct_text())
    assert package.covered_character_count == package.character_count
    assert package.coverage_ratio == 1.0
    assert tuple(unit.index for unit in package.units) == tuple(range(package.unit_count))
    assert len({unit.unit_id for unit in package.units}) == package.unit_count
    for unit, chunk in zip(package.units, preparation.chunk_plan.chunks):
        assert unit.index == chunk.index == unit.chunk_index
        assert unit.text == chunk.text
        assert (unit.source_character_start, unit.source_character_end) == (
            chunk.source_character_start,
            chunk.source_character_end,
        )
        assert unit.section_indices == chunk.section_indices
        assert unit.heading_text == chunk.heading_text
        assert unit.boundary_reason == chunk.boundary_reason
        assert unit.source_chunk_fingerprint == chunk.content_fingerprint
        assert unit.status == "prepared"
        assert unit.attempt_count == unit.provider_request_count == 0
        assert unit.translation_result_attached is False


def test_source_references_and_all_authorizations_are_explicit(tmp_path: Path) -> None:
    preparation = _ready_preparation(tmp_path)
    package = TranslationExecutionPackageBuilder().build(preparation)
    assert package.source.source_name == preparation.source_name
    assert package.source.source_content_fingerprint == preparation.source_content_fingerprint
    assert package.source.manifest_fingerprint == preparation.manifest_fingerprint
    assert package.source.segmentation_fingerprint == preparation.segmentation_fingerprint
    assert package.source.chunk_plan_fingerprint == preparation.chunk_plan_fingerprint
    assert package.source.preparation_fingerprint == preparation.preparation_fingerprint
    assert package.provider_execution_authorized is False
    assert package.translation_execution_authorized is False
    assert package.runtime_submission_authorized is False
    assert package.automatic_retry_authorized is False
    assert package.automatic_fallback_authorized is False
    assert package.output_replacement_authorized is False
    assert [finding.code for finding in package.findings] == [
        "EXECUTION_NOT_AUTHORIZED"
    ]


def test_ready_with_warnings_is_preserved_not_approved(tmp_path: Path) -> None:
    preparation = _ready_preparation(tmp_path)
    warning = BookPreparationFinding(
        code="CHUNKING_WARNING_PROPAGATED",
        severity="warning",
        message="warning",
        stage="chunking",
        observed_value="CHUNK_BELOW_MINIMUM",
    )
    preparation = _with_state(preparation, "ready_with_warnings", (warning,))
    package = TranslationExecutionPackageBuilder().build(preparation)
    assert package.status == "prepared_with_warnings"
    assert package.action == "hold_for_execution_authorization"
    assert [finding.code for finding in package.findings] == [
        "PREPARATION_WARNING_PROPAGATED",
        "EXECUTION_NOT_AUTHORIZED",
    ]


@pytest.mark.parametrize(
    ("status", "action", "code"),
    [
        ("manual_review", "manual_review", "PREPARATION_MANUAL_REVIEW_REJECTED"),
        ("blocked", "reject", "PREPARATION_BLOCKED_REJECTED"),
        ("unknown", "reject", "PREPARATION_BLOCKED_REJECTED"),
    ],
)
def test_non_ready_states_fail_closed_without_units(
    tmp_path: Path, status: str, action: str, code: str
) -> None:
    preparation = _with_state(_ready_preparation(tmp_path), status)
    with pytest.raises(InvalidPreparationStateError) as captured:
        TranslationExecutionPackageBuilder().build(preparation)
    assert captured.value.preparation_status == status
    assert captured.value.action == action
    assert code in captured.value.finding_codes
    assert preparation.reconstruct_text() not in str(captured.value)


def test_invalid_input_type_is_rejected() -> None:
    with pytest.raises(InvalidExecutionPackageInputError):
        TranslationExecutionPackageBuilder().build("raw novel text")


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("source_content_fingerprint", "SOURCE_FINGERPRINT_MISMATCH"),
        ("manifest_fingerprint", "MANIFEST_FINGERPRINT_MISMATCH"),
        ("segmentation_fingerprint", "SEGMENTATION_FINGERPRINT_MISMATCH"),
        ("chunk_plan_fingerprint", "CHUNK_PLAN_FINGERPRINT_MISMATCH"),
        ("preparation_fingerprint", "PREPARATION_FINGERPRINT_MISMATCH"),
    ],
)
def test_five_preparation_fingerprint_mismatches_fail_closed(
    tmp_path: Path, field: str, code: str
) -> None:
    preparation = replace(_ready_preparation(tmp_path), **{field: "0" * 64})
    with pytest.raises(ExecutionPackageConsistencyError) as captured:
        TranslationExecutionPackageBuilder().build(preparation)
    assert captured.value.finding.code == code


def test_chunk_count_index_fingerprint_and_section_mismatches_fail_closed(
    tmp_path: Path,
) -> None:
    preparation = _ready_preparation(tmp_path)
    builder = TranslationExecutionPackageBuilder()

    bad_plan = _corrupt(
        preparation.chunk_plan, chunk_count=preparation.chunk_plan.chunk_count + 1
    )
    with pytest.raises(ExecutionPackageConsistencyError) as count_error:
        builder.build(replace(preparation, chunk_plan=bad_plan))
    assert count_error.value.finding.code == "UNIT_COUNT_MISMATCH"

    for changes, code in (
        ({"index": 7}, "UNIT_INDEX_MISMATCH"),
        ({"content_fingerprint": "0" * 64}, "CHUNK_FINGERPRINT_MISMATCH"),
        ({"section_indices": (99,)}, "UNIT_SECTION_REFERENCE_MISMATCH"),
    ):
        chunks = list(preparation.chunk_plan.chunks)
        chunks[0] = _corrupt(chunks[0], **changes)
        bad_plan = _corrupt(preparation.chunk_plan, chunks=tuple(chunks))
        with pytest.raises(ExecutionPackageConsistencyError) as captured:
            builder.build(replace(preparation, chunk_plan=bad_plan))
        assert captured.value.finding.code == code


def test_gap_overlap_text_and_reconstruction_corruption_fail_closed(tmp_path: Path) -> None:
    preparation = _ready_preparation(tmp_path)
    builder = TranslationExecutionPackageBuilder()
    assert len(preparation.chunk_plan.chunks) >= 2

    cases = (
        (0, {"source_character_start": 1}, "UNIT_OFFSET_GAP"),
        (1, {"source_character_start": preparation.chunk_plan.chunks[1].source_character_start - 1}, "UNIT_OFFSET_OVERLAP"),
        (0, {"text": "changed"}, "UNIT_TEXT_MISMATCH"),
    )
    for chunk_index, changes, code in cases:
        chunks = list(preparation.chunk_plan.chunks)
        chunks[chunk_index] = _corrupt(chunks[chunk_index], **changes)
        bad_plan = _corrupt(preparation.chunk_plan, chunks=tuple(chunks))
        with pytest.raises(ExecutionPackageConsistencyError) as captured:
            builder.build(replace(preparation, chunk_plan=bad_plan))
        assert captured.value.finding.code == code


@pytest.mark.parametrize(
    "text",
    [
        "Chapter 1\r\n" + "  Whitespace is preserved.  \r\n\r\n" * 70 + "Chapter 2\r\n" + "Trailing content. " * 100 + "\r\n",
        "Chapter 1\n" + "e\u0301 combining sequence. " * 100 + "\nChapter 2\n" + "More English content. " * 100,
        "第一章\n" + "中文內容。" * 300 + "\n第二章\n" + "日本語の内容です。" * 200,
        "Chapter 1\n" + "English content. " * 120 + "\nChapter 2\n" + "More content. " * 140,
    ],
)
def test_multilingual_newline_whitespace_and_unicode_are_lossless(
    tmp_path: Path, text: str
) -> None:
    preparation = _ready_preparation(tmp_path, text)
    package = TranslationExecutionPackageBuilder().build(preparation)
    assert package.reconstruct_source_text() == text
    assert package.units[0].source_character_start == 0
    assert package.units[-1].source_character_end == len(text)
    assert all(
        left.source_character_end == right.source_character_start
        for left, right in zip(package.units, package.units[1:])
    )


def test_three_builds_and_canonical_serialization_are_identical(tmp_path: Path) -> None:
    preparation = _ready_preparation(tmp_path)
    builder = TranslationExecutionPackageBuilder()
    packages = tuple(builder.build(preparation) for _ in range(3))
    assert packages[0] == packages[1] == packages[2]
    assert packages[0].to_json() == packages[1].to_json() == packages[2].to_json()
    assert re.fullmatch(r"[0-9a-f]{64}", packages[0].execution_package_fingerprint)
    payload = json.loads(packages[0].to_json())
    observed = payload.pop("execution_package_fingerprint")
    assert observed not in json.dumps(payload, ensure_ascii=False)

