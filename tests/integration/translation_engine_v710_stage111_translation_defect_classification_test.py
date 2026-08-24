from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.translation_quality_corpus import GoldenReviewCase, load_golden_corpus, validate_golden_cases
from core.translation_quality_defects import DEFECT_CATEGORIES, SEVERITIES, initial_human_confirmed_defects, severity_rank, validate_category, validate_defect, validate_defects, validate_severity, verify_defect_artifact

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/te_v71_quality_framework"
ARTIFACT = FIXTURES / "TE_V71_STAGE111_TRANSLATION_DEFECTS.json"
CORPUS = ROOT / "archive/historical/quality_corpus/golden_review/te_v71_initial_defects.json"


@pytest.mark.parametrize("category", DEFECT_CATEGORIES)
def test_supported_categories(category: str) -> None:
    assert validate_category(category) == category


@pytest.mark.parametrize("severity", SEVERITIES)
def test_supported_severities_are_stably_ranked(severity: str) -> None:
    assert severity_rank(severity) == SEVERITIES.index(severity)
    assert validate_severity(severity) == severity


@pytest.mark.parametrize("bad", ["", "naturalness", "completeness"])
def test_unknown_category_rejected(bad: str) -> None:
    with pytest.raises(ValueError):
        validate_category(bad)


def test_six_human_confirmed_defects() -> None:
    rows = initial_human_confirmed_defects()
    assert len(rows) == 6 and all(row.human_confirmed for row in rows)


def test_primary_and_secondary_categories_are_distinct() -> None:
    assert all(row.category not in row.secondary_categories for row in initial_human_confirmed_defects())


def test_critical_omission_is_blocking() -> None:
    row = next(row for row in initial_human_confirmed_defects() if row.defect_id == "TQ-DEF-B")
    assert row.category == "omission" and row.severity == "critical" and row.blocking


def test_suggestions_are_not_approved_translations() -> None:
    assert all(row.metadata["approved_translation"] is None for row in initial_human_confirmed_defects())


def test_excerpt_size_is_bounded() -> None:
    assert all(len(value) <= 80 for row in initial_human_confirmed_defects() for value in (row.source_excerpt, row.translation_excerpt) if value)


def test_duplicate_defect_id_rejected() -> None:
    rows = initial_human_confirmed_defects()
    with pytest.raises(ValueError, match="duplicate"):
        validate_defects((rows[0], rows[0]))


def test_noncritical_blocking_rejected() -> None:
    with pytest.raises(ValueError, match="critical"):
        validate_defect(replace(initial_human_confirmed_defects()[0], blocking=True))


def test_artifact_integrity_and_boundaries() -> None:
    payload = verify_defect_artifact(ARTIFACT)
    assert payload["defect_count"] == 6 and payload["blocking_defect_count"] == 1
    assert payload["provider_execution_performed"] is False


def test_artifact_contains_exact_fixed_ids() -> None:
    payload = verify_defect_artifact(ARTIFACT)
    assert [row["defect_id"] for row in payload["defects"]] == [f"TQ-DEF-{letter}" for letter in "ABCDEF"]


def test_artifact_has_no_full_review_copy() -> None:
    assert len(ARTIFACT.read_text(encoding="utf-8")) < 15000


def test_golden_corpus_loads_six_confirmed_cases() -> None:
    cases = load_golden_corpus(CORPUS)
    assert len(cases) == 6 and all(row.human_confirmed for row in cases)


def test_golden_corpus_final_translations_are_null() -> None:
    assert all(row.approved_final_translation is None for row in load_golden_corpus(CORPUS))


def test_unreviewed_case_rejected() -> None:
    row = load_golden_corpus(CORPUS)[0]
    with pytest.raises(ValueError, match="unreviewed"):
        validate_golden_cases((replace(row, human_confirmed=False),))


def test_duplicate_corpus_id_rejected() -> None:
    row = load_golden_corpus(CORPUS)[0]
    with pytest.raises(ValueError, match="duplicate"):
        validate_golden_cases((row, row))


def test_defect_artifact_tamper_fails(tmp_path: Path) -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8")); payload["defect_count"] = 7
    path = tmp_path / "tampered.json"; path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        verify_defect_artifact(path)
