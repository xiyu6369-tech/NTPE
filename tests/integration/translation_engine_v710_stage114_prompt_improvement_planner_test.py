from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.translation_prompt_improvement_planner import DEFECT_PLAN_MAPPING, IMPLEMENTATION_STATUS, PROMPT_SECTIONS, RISK_DESCRIPTIONS, RISK_LEVELS, create_prompt_improvement_plans, validate_plans, verify_improvement_plan_artifact
from core.translation_quality_defects import initial_human_confirmed_defects
from core.translation_quality_metrics import calculate_quality_metrics

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/te_v71_quality_framework"
ARTIFACT = FIXTURES / "TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json"


def _plans():
    defects = initial_human_confirmed_defects()
    return create_prompt_improvement_plans(defects, calculate_quality_metrics(defects))


@pytest.mark.parametrize("section", PROMPT_SECTIONS)
def test_supported_prompt_sections(section: str) -> None:
    assert section in PROMPT_SECTIONS


@pytest.mark.parametrize("risk", RISK_LEVELS)
def test_supported_risks_have_descriptions(risk: str) -> None:
    assert RISK_DESCRIPTIONS[risk]


@pytest.mark.parametrize("defect_id", [f"TQ-DEF-{letter}" for letter in "ABCDEF"])
def test_each_fixed_defect_has_mapping(defect_id: str) -> None:
    assert defect_id in DEFECT_PLAN_MAPPING


@pytest.mark.parametrize("defect_id", [f"TQ-DEF-{letter}" for letter in "ABCDEF"])
def test_each_fixed_defect_has_independent_plan(defect_id: str) -> None:
    matches = [row for row in _plans() if row.related_defect_ids == (defect_id,)]
    assert len(matches) == 1


@pytest.mark.parametrize("plan_id", [f"TQ-PLAN-{index:02d}" for index in range(1, 7)])
def test_all_plans_are_unapplied_and_require_approval(plan_id: str) -> None:
    plan = next(row for row in _plans() if row.plan_id == plan_id)
    assert plan.implementation_status == IMPLEMENTATION_STATUS
    assert plan.requires_human_approval is True


def test_planner_is_deterministic() -> None:
    assert _plans() == _plans()


def test_plans_reference_metric_evidence() -> None:
    assert len(_plans()) == 6


def test_low_risk_does_not_auto_approve() -> None:
    low = next(row for row in _plans() if row.risk_level == "low")
    assert low.requires_human_approval and low.implementation_status == "planned_not_applied"


def test_no_measured_percentage_claims() -> None:
    rendered = json.dumps([row.to_dict() for row in _plans()])
    assert "%" not in rendered and "measured improvement" not in rendered


def test_missing_human_approval_rejected() -> None:
    with pytest.raises(ValueError, match="approved or applied"):
        validate_plans((replace(_plans()[0], requires_human_approval=False),))


def test_applied_status_rejected() -> None:
    with pytest.raises(ValueError, match="approved or applied"):
        validate_plans((replace(_plans()[0], implementation_status="applied"),))


def test_unknown_section_rejected() -> None:
    with pytest.raises(ValueError, match="section"):
        validate_plans((replace(_plans()[0], target_prompt_section="system_prompt"),))


def test_artifact_integrity_and_nonclaims() -> None:
    payload = verify_improvement_plan_artifact(ARTIFACT)
    assert len(payload["plans"]) == 6 and payload["plans_applied"] == 0


def test_artifact_matches_planner() -> None:
    assert verify_improvement_plan_artifact(ARTIFACT)["plans"] == [row.to_dict() for row in _plans()]


def test_tampered_artifact_rejected(tmp_path: Path) -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8")); payload["plans_applied"] = 1
    path = tmp_path / "bad.json"; path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        verify_improvement_plan_artifact(path)
