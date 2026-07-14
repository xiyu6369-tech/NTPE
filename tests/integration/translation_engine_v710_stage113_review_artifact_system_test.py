from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.translation_quality_defects import initial_human_confirmed_defects
from core.translation_quality_metrics import calculate_quality_metrics
from core.translation_quality_review_artifacts import FORBIDDEN_REVIEW_KEYS, StructuredReview, assert_review_redacted, build_structured_review, review_summary, validate_review, verify_review_artifact

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ARTIFACT = ROOT / "artifacts/te_v7_stage10101/TE_V7_STAGE10101_CONTROLLED_RETRY.json"
SOURCE_REVIEW = ROOT / "artifacts/te_v7_stage10101/review/TE_V7_STAGE10101_TRANSLATION_REVIEW.txt"
STAGE_DIR = ROOT / "artifacts/te_v71_stage113"


def _review() -> StructuredReview:
    return build_structured_review(SOURCE_ARTIFACT, SOURCE_REVIEW, initial_human_confirmed_defects(), calculate_quality_metrics(initial_human_confirmed_defects()))


@pytest.mark.parametrize("field", sorted(FORBIDDEN_REVIEW_KEYS))
def test_forbidden_review_fields_rejected(field: str) -> None:
    with pytest.raises(ValueError, match="forbidden"):
        assert_review_redacted({field: "secret"})


@pytest.mark.parametrize("name", ["TE_V71_STAGE113_REVIEW.json","TE_V71_STAGE113_REVIEW_SUMMARY.json","TE_V71_STAGE113_REVIEW_METRICS.json","TE_V71_STAGE113_REVIEW_DEFECTS.json"])
def test_structured_artifact_set_exists_and_verifies(name: str) -> None:
    payload = verify_review_artifact(STAGE_DIR / name)
    assert payload["stage"] == "TE-v7.1-Stage11.3"


@pytest.mark.parametrize("dimension", ["naturalness","fidelity","completeness","narrative","consistency","traditional_chinese_style","readability"])
def test_reviewed_dimensions_are_evidence_backed(dimension: str) -> None:
    assert dimension in _review().reviewed_dimensions


@pytest.mark.parametrize("field", ["human_review_required","human_review_completed","content_redacted"])
def test_required_review_flags_are_true(field: str) -> None:
    assert getattr(_review(), field) is True


@pytest.mark.parametrize("field", ["quality_pass","new_translation_generated","provider_executed_in_this_stage"])
def test_required_nonclaims_are_false(field: str) -> None:
    assert getattr(_review(), field) is False


def test_source_hashes_are_exact() -> None:
    review = _review()
    assert review.source_artifact_sha256 == hashlib.sha256(SOURCE_ARTIFACT.read_bytes()).hexdigest()
    assert review.source_review_sha256 == hashlib.sha256(SOURCE_REVIEW.read_bytes()).hexdigest()


def test_review_txt_is_not_reclassified_as_translation() -> None:
    review = _review()
    assert review.review_type == "human_translation_quality_review" and review.review_origin == "stage10101_review_txt"


def test_review_counts_match_evidence() -> None:
    review = _review()
    assert review.defect_count == 6 and review.blocking_defect_count == 1


def test_summary_preserves_nonclaims() -> None:
    summary = review_summary(_review())
    assert summary["new_translation_generated"] is False and summary["provider_executed_in_this_stage"] is False


@pytest.mark.parametrize("change", [{"quality_pass":True},{"human_review_completed":False},{"content_redacted":False},{"new_translation_generated":True},{"provider_executed_in_this_stage":True},{"blocking_defect_count":0}])
def test_invalid_review_boundaries_rejected(change: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        validate_review(replace(_review(), **change))


def test_nested_safe_payload_is_accepted() -> None:
    assert_review_redacted({"review": {"defect_ids": ["TQ-DEF-A"]}})


def test_existing_review_txt_bytes_unchanged_by_builder() -> None:
    before = SOURCE_REVIEW.read_bytes(); _review(); assert SOURCE_REVIEW.read_bytes() == before


def test_tampered_review_artifact_rejected(tmp_path: Path) -> None:
    source = STAGE_DIR / "TE_V71_STAGE113_REVIEW.json"
    payload = json.loads(source.read_text(encoding="utf-8")); payload["quality_pass"] = True
    path = tmp_path / "bad.json"; path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        verify_review_artifact(path)
