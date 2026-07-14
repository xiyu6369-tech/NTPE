from __future__ import annotations

import json
from collections.abc import Mapping

from .decision_model import HumanReviewDecision, ReviewerProvenance
from .decision_schema import REQUIRED_FIELDS, REVIEWER_FIELDS
from .decision_validator import validate_review_decision
from .review_status import ReviewDecisionStatus


def serialize_review_decision(decision: HumanReviewDecision) -> str:
    validate_review_decision(decision)
    return json.dumps(decision.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def deserialize_review_decision(payload: str | bytes | Mapping[str, object]) -> HumanReviewDecision:
    raw = json.loads(payload) if isinstance(payload, (str, bytes, bytearray)) else dict(payload)
    if set(raw) != set(REQUIRED_FIELDS):
        raise ValueError("review decision schema fields invalid")
    reviewer = raw.get("reviewer")
    if not isinstance(reviewer, dict) or set(reviewer) != set(REVIEWER_FIELDS):
        raise ValueError("reviewer provenance schema invalid")
    try:
        decision = HumanReviewDecision(
            decision_id=str(raw["decision_id"]), review_id=str(raw["review_id"]),
            decision=ReviewDecisionStatus(str(raw["decision"])), decision_source=str(raw["decision_source"]),
            reviewer=ReviewerProvenance(str(reviewer["reviewer_id"]), str(reviewer["display_name"])),
            schema_version=str(raw["schema_version"]), created_at=str(raw["created_at"]),
            decision_reason=str(raw["decision_reason"]), review_artifact_sha256=str(raw["review_artifact_sha256"]),
            metrics_sha256=str(raw["metrics_sha256"]), defects_sha256=str(raw["defects_sha256"]),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("review decision payload invalid") from exc
    return validate_review_decision(decision)

