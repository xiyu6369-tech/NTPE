from __future__ import annotations

import hashlib

from .decision_model import HumanReviewDecision, ReviewerProvenance
from .decision_schema import DECISION_SOURCE, SCHEMA_VERSION
from .decision_validator import validate_review_decision
from .review_status import ReviewDecisionStatus


def build_review_decision(
    *,
    review_id: str,
    decision: ReviewDecisionStatus | str,
    reviewer: ReviewerProvenance,
    created_at: str,
    decision_reason: str,
    review_artifact_sha256: str,
    metrics_sha256: str,
    defects_sha256: str,
) -> HumanReviewDecision:
    try:
        status = decision if isinstance(decision, ReviewDecisionStatus) else ReviewDecisionStatus(decision)
    except ValueError as exc:
        raise ValueError("unsupported review decision status") from exc
    identity = "\n".join((review_id, status.value, reviewer.reviewer_id, created_at, decision_reason, review_artifact_sha256, metrics_sha256, defects_sha256))
    decision_id = "TQ-DEC-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20].upper()
    return validate_review_decision(HumanReviewDecision(
        decision_id=decision_id,
        review_id=review_id,
        decision=status,
        decision_source=DECISION_SOURCE,
        reviewer=reviewer,
        schema_version=SCHEMA_VERSION,
        created_at=created_at,
        decision_reason=decision_reason,
        review_artifact_sha256=review_artifact_sha256,
        metrics_sha256=metrics_sha256,
        defects_sha256=defects_sha256,
    ))

