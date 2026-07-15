from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ntpe.quality import build_review_view


ROOT = Path(__file__).resolve().parents[3]
REVIEW = ROOT / "artifacts/te_v71_stage113/TE_V71_STAGE113_REVIEW.json"
PLANS = ROOT / "artifacts/te_v71_stage114/TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json"
DECISION = ROOT / "artifacts/te_v71_stage115/TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json"


def test_review_view_preserves_plans_and_human_provenance() -> None:
    view = build_review_view(review_artifact=REVIEW, improvement_plans=PLANS, human_decision=DECISION)
    assert len(view.improvement_plans) == 6
    assert {plan.implementation_status for plan in view.improvement_plans} == {"planned_not_applied"}
    assert view.human_decision is not None
    assert view.human_decision.decision_source == "human_review"
    assert view.human_decision.reviewer.reviewer_id == "human-reviewer-001"
    assert view.plans_applied is view.decision_applied is view.corpus_approval_granted is False
    assert view.human_approval_required is True


def test_accepted_decision_is_not_corpus_approval_or_application() -> None:
    view = build_review_view(review_artifact=REVIEW, improvement_plans=PLANS, human_decision=DECISION)
    assert view.human_decision is not None and view.human_decision.decision.value == "accepted"
    assert not view.corpus_approval_granted
    assert not view.decision_applied


def test_review_view_is_deterministic_and_does_not_create_a_decision() -> None:
    first = build_review_view(review_artifact=REVIEW, improvement_plans=PLANS)
    second = build_review_view(review_artifact=REVIEW, improvement_plans=PLANS)
    assert first == second
    assert first.human_decision is None


def test_invalid_decision_reference_fails_closed() -> None:
    view = build_review_view(review_artifact=REVIEW, improvement_plans=PLANS, human_decision=DECISION)
    assert view.human_decision is not None
    wrong = replace(view.human_decision, review_id="OTHER-REVIEW")
    with pytest.raises(ValueError, match="different review"):
        build_review_view(review_artifact=REVIEW, improvement_plans=PLANS, human_decision=wrong)

