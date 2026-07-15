from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from core.translation_quality_defects import verify_defect_artifact
from core.translation_quality_metrics import verify_quality_metrics_artifact
from ntpe.quality import assess


ROOT = Path(__file__).resolve().parents[3]
DEFECTS = ROOT / "artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json"
METRICS = ROOT / "artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json"


def test_assessment_reads_frozen_models_and_serialized_artifacts_with_parity() -> None:
    artifact_view = assess(defects=DEFECTS, metrics=METRICS)
    model_view = assess(
        defects=tuple(artifact_view.defects),
        metrics=tuple(artifact_view.metrics),
    )
    assert artifact_view.blocking_defect_count == model_view.blocking_defect_count == 1
    assert artifact_view.overall_score == model_view.overall_score == 41.91
    assert artifact_view.quality_pass is model_view.quality_pass is False
    assert artifact_view.insufficient_evidence_dimensions == model_view.insufficient_evidence_dimensions == ("dialogue", "terminology")


def test_assessment_matches_legacy_verified_payloads() -> None:
    defects = verify_defect_artifact(DEFECTS)
    metrics = verify_quality_metrics_artifact(METRICS)
    view = assess(defects=DEFECTS, metrics=METRICS)
    assert len(view.defects) == defects["defect_count"]
    assert view.blocking_defect_count == defects["blocking_defect_count"]
    assert view.quality_pass == metrics["quality_pass"]
    assert view.overall_score == next(row["score"] for row in metrics["metrics"] if row["dimension"] == "overall")


def test_assessment_does_not_modify_mapping_inputs() -> None:
    defects = json.loads(DEFECTS.read_text(encoding="utf-8"))
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    before = copy.deepcopy((defects, metrics))
    assess(defects=defects, metrics=metrics)
    assert (defects, metrics) == before


def test_assessment_fails_closed_on_tampering_and_blocking_mismatch() -> None:
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    metrics["quality_pass"] = True
    with pytest.raises(ValueError, match="integrity"):
        assess(defects=DEFECTS, metrics=metrics)

