from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.translation_quality_defects import initial_human_confirmed_defects
from core.translation_quality_metrics import DIMENSION_WEIGHTS, QUALITY_DIMENSIONS, SEVERITY_PENALTIES, QualityMetricsConfig, calculate_quality_metrics, defects_for_dimension, score_evidence, validate_dimension, verify_quality_metrics_artifact

ROOT = Path(__file__).resolve().parents[2]
METRICS = ROOT / "artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json"
SUMMARY = ROOT / "artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_SUMMARY.json"


@pytest.mark.parametrize("dimension", QUALITY_DIMENSIONS)
def test_required_dimensions_supported(dimension: str) -> None:
    assert validate_dimension(dimension) == dimension


@pytest.mark.parametrize("severity,penalty", SEVERITY_PENALTIES.items())
def test_severity_penalties_are_distinct(severity: str, penalty: float) -> None:
    assert penalty > 0 and SEVERITY_PENALTIES["critical"] > SEVERITY_PENALTIES["low"]


@pytest.mark.parametrize("dimension", tuple(DIMENSION_WEIGHTS))
def test_dimension_weights_are_positive(dimension: str) -> None:
    assert 0 < DIMENSION_WEIGHTS[dimension] < 1


@pytest.mark.parametrize("defect_id,dimension", [("TQ-DEF-A","naturalness"),("TQ-DEF-B","completeness"),("TQ-DEF-C","fidelity"),("TQ-DEF-D","fidelity"),("TQ-DEF-E","narrative"),("TQ-DEF-F","traditional_chinese_style")])
def test_defect_evidence_mapping(defect_id: str, dimension: str) -> None:
    assert defect_id in {row.defect_id for row in defects_for_dimension(dimension, initial_human_confirmed_defects())}


def test_metrics_are_deterministic() -> None:
    assert calculate_quality_metrics(initial_human_confirmed_defects()) == calculate_quality_metrics(initial_human_confirmed_defects())


def test_critical_omission_reduces_completeness() -> None:
    metric = {row.dimension: row for row in calculate_quality_metrics(initial_human_confirmed_defects())}["completeness"]
    assert metric.score < 50 and metric.blocking_defect_count == 1


def test_semantic_mistranslation_reduces_fidelity() -> None:
    metric = {row.dimension: row for row in calculate_quality_metrics(initial_human_confirmed_defects())}["fidelity"]
    assert "TQ-DEF-C" in metric.related_defect_ids and metric.score < 50


def test_low_style_penalty_is_less_than_critical() -> None:
    defects = initial_human_confirmed_defects()
    assert score_evidence((defects[-1],)) > score_evidence((defects[1],))


def test_unreviewed_dimensions_are_not_full_score() -> None:
    rows = {row.dimension: row for row in calculate_quality_metrics(initial_human_confirmed_defects())}
    assert rows["dialogue"].status == "insufficient_evidence" and rows["dialogue"].score == 50
    assert rows["terminology"].status == "insufficient_evidence"


def test_overall_is_weighted_and_blocking() -> None:
    overall = calculate_quality_metrics(initial_human_confirmed_defects())[-1]
    assert overall.dimension == "overall" and overall.score <= 49 and overall.status == "blocking"


def test_no_defects_yields_insufficient_evidence_not_full_scores() -> None:
    rows = calculate_quality_metrics(())
    assert all(row.score == 50 for row in rows[:-1])
    assert all(row.status == "insufficient_evidence" for row in rows[:-1])


def test_config_is_fail_closed() -> None:
    with pytest.raises(ValueError):
        QualityMetricsConfig(passing_score=40, blocking_overall_cap=50)


def test_metrics_artifact_integrity_and_boundaries() -> None:
    payload = verify_quality_metrics_artifact(METRICS)
    assert payload["quality_pass"] is False and payload["human_review_based"] is True


def test_summary_integrity_and_evidence_gaps() -> None:
    payload = verify_quality_metrics_artifact(SUMMARY)
    assert payload["insufficient_evidence_dimensions"] == ["dialogue", "terminology"]


def test_metric_artifact_matches_computation() -> None:
    payload = verify_quality_metrics_artifact(METRICS)
    expected = [row.to_dict() for row in calculate_quality_metrics(initial_human_confirmed_defects())]
    assert payload["metrics"] == expected


def test_tampered_metric_artifact_rejected(tmp_path: Path) -> None:
    payload = json.loads(METRICS.read_text(encoding="utf-8")); payload["quality_pass"] = True
    path = tmp_path / "bad.json"; path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        verify_quality_metrics_artifact(path)
