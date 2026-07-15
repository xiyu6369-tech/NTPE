"""Public read-only quality review view."""

from __future__ import annotations

from .compatibility import decision_input, plans_input, review_input
from .models import QualityReview


def build_review_view(
    *,
    review_artifact: object,
    improvement_plans: object,
    human_decision: object | None = None,
) -> QualityReview:
    review, review_refs = review_input(review_artifact)
    plans, plans_applied, approval_required, plan_refs = plans_input(improvement_plans)
    decision, decision_applied, decision_refs = decision_input(human_decision)
    if decision is not None and decision.review_id != review.review_id:
        raise ValueError("human decision references a different review")
    return QualityReview(
        review=review,
        improvement_plans=plans,
        human_decision=decision,
        plans_applied=plans_applied,
        decision_applied=decision_applied,
        human_approval_required=approval_required,
        source_references=review_refs + plan_refs + decision_refs,
        corpus_approval_granted=False,
    )

