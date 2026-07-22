from __future__ import annotations

import copy
import hashlib
import re
from dataclasses import replace
from pathlib import Path

import pytest

from core.book_chunking import BookChunkPlanner
from core.book_intake import (
    BookIntakeManifestBuilder,
    BookIntakeProcessor,
    BookPreflightAnalyzer,
)
from core.book_intake.errors import DecodeFailedError, FileNotFoundError as IntakeFileNotFoundError
from core.book_preparation import (
    BookPreparationBlockedError,
    BookPreparationConsistencyError,
    BookPreparationProcessor,
    BookPreparationStageError,
    InvalidBookPreparationInputError,
)
from core.book_segmentation import BookStructureSegmenter


_ACTIONS = {
    "ready": "proceed",
    "ready_with_warnings": "proceed_with_warning",
    "manual_review": "manual_review",
    "manual_review_required": "manual_review",
    "blocked": "reject",
}


def _raw_bundle(tmp_path: Path, text: str = "Chapter 1\n" + "Text. " * 220):
    path = tmp_path / "book.txt"
    path.write_text(text, encoding="utf-8", newline="")
    intake = BookIntakeProcessor().process(path)
    preflight = BookPreflightAnalyzer().analyze(intake)
    manifest = BookIntakeManifestBuilder().build(intake, preflight)
    segmentation = BookStructureSegmenter().segment(intake, manifest=manifest)
    chunk_plan = BookChunkPlanner().plan(segmentation)
    return intake, preflight, manifest, segmentation, chunk_plan


def _bundle_with_statuses(
    tmp_path: Path,
    *,
    intake_status: str = "ready",
    preflight_status: str = "ready",
    segmentation_status: str = "ready",
    chunk_status: str = "ready",
):
    intake, preflight, _, segmentation, chunk_plan = _raw_bundle(tmp_path)
    intake = replace(
        intake,
        status=intake_status,
        recommended_action=_ACTIONS[intake_status],
    )
    preflight = replace(
        preflight,
        status=preflight_status,
        recommended_action=_ACTIONS[preflight_status],
        risk_findings=(),
    )
    manifest = BookIntakeManifestBuilder().build(intake, preflight)
    segmentation = replace(
        segmentation,
        status=segmentation_status,
        action=_ACTIONS[segmentation_status],
        findings=(),
    )
    chunk_plan = replace(
        chunk_plan,
        status=chunk_status,
        action=_ACTIONS[chunk_status],
        findings=(),
    )
    return intake, preflight, manifest, segmentation, chunk_plan


class _Dependency:
    def __init__(self, name, result, events):
        self.name = name
        self.result = result
        self.events = events
        self.calls = 0

    def _call(self):
        self.calls += 1
        self.events.append(self.name)
        return self.result

    def process(self, source_path):
        return self._call()

    def analyze(self, intake):
        return self._call()

    def build(self, intake, preflight):
        return self._call()

    def segment(self, intake, *, manifest):
        return self._call()

    def plan(self, segmentation):
        return self._call()


def _injected_processor(bundle, events=None):
    events = [] if events is None else events
    dependencies = tuple(
        _Dependency(name, result, events)
        for name, result in zip(
            ("intake", "preflight", "manifest", "segmentation", "chunking"),
            bundle,
        )
    )
    return (
        BookPreparationProcessor(
            intake_processor=dependencies[0],
            preflight_analyzer=dependencies[1],
            manifest_builder=dependencies[2],
            segmenter=dependencies[3],
            chunk_planner=dependencies[4],
        ),
        dependencies,
        events,
    )


def test_prepare_runs_each_dependency_once_in_fixed_order(tmp_path: Path) -> None:
    bundle = _bundle_with_statuses(tmp_path)
    processor, dependencies, events = _injected_processor(bundle)
    result = processor.prepare(tmp_path / "unused.txt")
    assert events == ["intake", "preflight", "manifest", "segmentation", "chunking"]
    assert [item.calls for item in dependencies] == [1, 1, 1, 1, 1]
    assert result.intake_result is bundle[0]
    assert result.preflight_result is bundle[1]
    assert result.intake_manifest is bundle[2]
    assert result.segmentation_result is bundle[3]
    assert result.chunk_plan is bundle[4]


def test_prepare_intake_skips_intake_and_produces_same_downstream_result(tmp_path: Path) -> None:
    bundle = _bundle_with_statuses(tmp_path)
    processor, dependencies, events = _injected_processor(bundle)
    result = processor.prepare_intake(bundle[0])
    assert events == ["preflight", "manifest", "segmentation", "chunking"]
    assert dependencies[0].calls == 0
    assert result.reconstruct_text() == bundle[0].text


def test_default_dependencies_run_the_complete_pipeline(tmp_path: Path) -> None:
    path = tmp_path / "default.txt"
    path.write_bytes(("Chapter 1\n" + "Sentence. " * 150).encode("utf-8"))
    result = BookPreparationProcessor().prepare(path)
    assert result.reconstruct_text() == path.read_bytes().decode("utf-8")
    assert result.source_name == "default.txt"


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (("ready", "ready", "ready", "ready"), "ready"),
        (("ready_with_warnings", "ready", "ready", "ready"), "ready_with_warnings"),
        (("ready", "ready_with_warnings", "ready", "ready"), "ready_with_warnings"),
        (("ready", "ready", "ready_with_warnings", "ready"), "ready_with_warnings"),
        (("ready", "ready", "ready", "ready_with_warnings"), "ready_with_warnings"),
        (("ready_with_warnings", "manual_review_required", "ready", "ready"), "manual_review"),
        (("ready", "ready", "manual_review", "ready_with_warnings"), "manual_review"),
    ],
)
def test_status_aggregation_never_hides_more_severe_stage(tmp_path: Path, statuses, expected) -> None:
    bundle = _bundle_with_statuses(
        tmp_path,
        intake_status=statuses[0],
        preflight_status=statuses[1],
        segmentation_status=statuses[2],
        chunk_status=statuses[3],
    )
    processor, _, _ = _injected_processor(bundle)
    result = processor.prepare_intake(bundle[0])
    assert result.status == expected
    assert result.action == _ACTIONS[expected]


@pytest.mark.parametrize(
    ("stage_index", "status", "finding_code"),
    [
        (0, "ready_with_warnings", "INTAKE_WARNING_PROPAGATED"),
        (1, "ready_with_warnings", "PREFLIGHT_WARNING_PROPAGATED"),
        (2, "ready_with_warnings", "SEGMENTATION_WARNING_PROPAGATED"),
        (3, "ready_with_warnings", "CHUNKING_WARNING_PROPAGATED"),
        (2, "manual_review", "MANUAL_REVIEW_REQUIRED"),
    ],
)
def test_upstream_status_findings_are_aggregated_once(tmp_path: Path, stage_index, status, finding_code) -> None:
    values = ["ready", "ready", "ready", "ready"]
    values[stage_index] = status
    bundle = _bundle_with_statuses(
        tmp_path,
        intake_status=values[0],
        preflight_status=values[1],
        segmentation_status=values[2],
        chunk_status=values[3],
    )
    result = _injected_processor(bundle)[0].prepare_intake(bundle[0])
    codes = [item.code for item in result.findings]
    assert codes.count(finding_code) == 1
    assert all(bundle[0].text not in item.message for item in result.findings)


def test_intake_blocked_stops_every_downstream_stage(tmp_path: Path) -> None:
    bundle = list(_bundle_with_statuses(tmp_path))
    bundle[0] = replace(bundle[0], status="blocked", recommended_action="reject")
    processor, dependencies, events = _injected_processor(tuple(bundle))
    with pytest.raises(BookPreparationBlockedError) as captured:
        processor.prepare(tmp_path / "unused.txt")
    assert captured.value.intake_result is bundle[0]
    assert events == ["intake"]
    assert [item.calls for item in dependencies] == [1, 0, 0, 0, 0]


def test_preflight_blocked_stops_manifest_and_structural_stages(tmp_path: Path) -> None:
    bundle = list(_bundle_with_statuses(tmp_path))
    bundle[1] = replace(bundle[1], status="blocked", recommended_action="reject")
    processor, dependencies, events = _injected_processor(tuple(bundle))
    with pytest.raises(BookPreparationBlockedError) as captured:
        processor.prepare_intake(bundle[0])
    assert captured.value.preflight_result is bundle[1]
    assert events == ["preflight"]
    assert [item.calls for item in dependencies] == [0, 1, 0, 0, 0]


def test_cross_stage_text_and_fingerprint_mismatches_fail_closed(tmp_path: Path) -> None:
    bundle = list(_bundle_with_statuses(tmp_path))
    other = _raw_bundle(tmp_path, "Chapter 1\nDifferent source. " * 20)
    bundle[3], bundle[4] = other[3], other[4]
    with pytest.raises(BookPreparationConsistencyError) as text_error:
        _injected_processor(tuple(bundle))[0].prepare_intake(bundle[0])
    assert text_error.value.finding.code == "SOURCE_CONTENT_MISMATCH"

    bundle = list(_bundle_with_statuses(tmp_path))
    bundle[3] = replace(bundle[3], source_content_fingerprint="0" * 64)
    with pytest.raises(BookPreparationConsistencyError) as fingerprint_error:
        _injected_processor(tuple(bundle))[0].prepare_intake(bundle[0])
    assert fingerprint_error.value.finding.code == "CONTENT_FINGERPRINT_MISMATCH"


def test_source_name_manifest_and_segmentation_fingerprint_mismatches_fail_closed(tmp_path: Path) -> None:
    bundle = list(_bundle_with_statuses(tmp_path))
    bundle[3] = replace(bundle[3], source_name="other.txt")
    with pytest.raises(BookPreparationConsistencyError) as name_error:
        _injected_processor(tuple(bundle))[0].prepare_intake(bundle[0])
    assert name_error.value.finding.code == "SOURCE_NAME_MISMATCH"

    bundle = list(_bundle_with_statuses(tmp_path))
    bad_manifest = copy.copy(bundle[2])
    object.__setattr__(bad_manifest, "status", "ready_with_warnings")
    bundle[2] = bad_manifest
    with pytest.raises(BookPreparationConsistencyError) as manifest_error:
        _injected_processor(tuple(bundle))[0].prepare_intake(bundle[0])
    assert manifest_error.value.finding.code == "MANIFEST_STATUS_MISMATCH"

    bundle = list(_bundle_with_statuses(tmp_path))
    bundle[4] = replace(bundle[4], segmentation_fingerprint="0" * 64)
    with pytest.raises(BookPreparationConsistencyError) as segmentation_error:
        _injected_processor(tuple(bundle))[0].prepare_intake(bundle[0])
    assert segmentation_error.value.finding.code == "SEGMENTATION_FINGERPRINT_MISMATCH"


def test_character_section_and_chunk_count_mismatches_fail_closed(tmp_path: Path) -> None:
    bundle = list(_bundle_with_statuses(tmp_path))
    bundle[3] = replace(bundle[3], character_count=bundle[3].character_count + 1)
    with pytest.raises(BookPreparationConsistencyError) as character_error:
        _injected_processor(tuple(bundle))[0].prepare_intake(bundle[0])
    assert character_error.value.finding.code == "CHARACTER_COUNT_MISMATCH"

    bundle = list(_bundle_with_statuses(tmp_path))
    bundle[4] = replace(bundle[4], section_count=bundle[4].section_count + 1)
    with pytest.raises(BookPreparationConsistencyError) as section_error:
        _injected_processor(tuple(bundle))[0].prepare_intake(bundle[0])
    assert section_error.value.finding.code == "SECTION_COUNT_MISMATCH"

    bundle = list(_bundle_with_statuses(tmp_path))
    bad_plan = copy.copy(bundle[4])
    object.__setattr__(bad_plan, "chunk_count", bad_plan.chunk_count + 1)
    bundle[4] = bad_plan
    with pytest.raises(BookPreparationConsistencyError) as chunk_error:
        _injected_processor(tuple(bundle))[0].prepare_intake(bundle[0])
    assert chunk_error.value.finding.code == "CHUNK_COUNT_MISMATCH"


def test_invalid_input_and_downstream_exception_behavior(tmp_path: Path) -> None:
    with pytest.raises(InvalidBookPreparationInputError):
        BookPreparationProcessor().prepare_intake("invalid")
    bundle = _bundle_with_statuses(tmp_path)

    class BrokenPreflight:
        def analyze(self, intake):
            raise RuntimeError("injected failure")

    processor = BookPreparationProcessor(preflight_analyzer=BrokenPreflight())
    with pytest.raises(BookPreparationStageError) as captured:
        processor.prepare_intake(bundle[0])
    assert captured.value.stage == "preflight"
    assert isinstance(captured.value.__cause__, RuntimeError)


def test_original_intake_exceptions_remain_recognizable(tmp_path: Path) -> None:
    with pytest.raises(IntakeFileNotFoundError):
        BookPreparationProcessor().prepare(tmp_path / "missing.txt")
    with pytest.raises(Exception) as directory_error:
        BookPreparationProcessor().prepare(tmp_path)
    assert directory_error.value.__class__.__module__ == "core.book_intake.errors"

    class BrokenIntake:
        def process(self, path):
            raise DecodeFailedError("decode failed")

    with pytest.raises(DecodeFailedError):
        BookPreparationProcessor(intake_processor=BrokenIntake()).prepare(tmp_path / "x.txt")


def test_preparation_fingerprint_is_deterministic_and_content_sensitive(tmp_path: Path) -> None:
    bundle = _bundle_with_statuses(tmp_path)
    processor, _, _ = _injected_processor(bundle)
    results = [processor.prepare_intake(bundle[0]) for _ in range(3)]
    assert results[0] == results[1] == results[2]
    assert re.fullmatch(r"[0-9a-f]{64}", results[0].preparation_fingerprint)
    assert results[0].source_content_fingerprint == hashlib.sha256(bundle[0].text.encode("utf-8")).hexdigest()

    warning_bundle = _bundle_with_statuses(tmp_path, chunk_status="ready_with_warnings")
    warning_result = _injected_processor(warning_bundle)[0].prepare_intake(warning_bundle[0])
    assert warning_result.preparation_fingerprint != results[0].preparation_fingerprint
