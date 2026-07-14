from __future__ import annotations

from datetime import datetime

from .decision_model import HumanReviewDecision
from .decision_schema import DECISION_SOURCE, SCHEMA_VERSION
from .integrity import SHA256_PATTERN
from .review_status import ReviewDecisionStatus

FORBIDDEN_IDENTITY_VALUES = {
    "system", "automatic", "provider", "runtime", "planner", "metrics",
    "quality_engine", "model", "llm",
}


def _non_automated_identity(value: str) -> bool:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    tokens = set(normalized.split("_"))
    return bool(normalized) and normalized not in FORBIDDEN_IDENTITY_VALUES and tokens.isdisjoint(FORBIDDEN_IDENTITY_VALUES)


def validate_review_decision(decision: HumanReviewDecision) -> HumanReviewDecision:
    if not decision.decision_id.strip() or not decision.review_id.strip():
        raise ValueError("decision and review identifiers are required")
    if not isinstance(decision.decision, ReviewDecisionStatus):
        raise ValueError("unsupported review decision status")
    if decision.decision_source != DECISION_SOURCE:
        raise ValueError("decision source must be human_review")
    if not _non_automated_identity(decision.reviewer.reviewer_id) or not _non_automated_identity(decision.reviewer.display_name):
        raise ValueError("reviewer provenance must identify a human reviewer")
    if decision.schema_version != SCHEMA_VERSION:
        raise ValueError("unsupported review decision schema version")
    try:
        parsed = datetime.fromisoformat(decision.created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("created_at must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("created_at must include a timezone")
    reason = decision.decision_reason.strip()
    if len(reason) < 12 or reason.upper() in {"PASS", "OK", "ACCEPTED"}:
        raise ValueError("a substantive human decision reason is required")
    for digest in (decision.review_artifact_sha256, decision.metrics_sha256, decision.defects_sha256):
        if SHA256_PATTERN.fullmatch(digest) is None:
            raise ValueError("review integrity references must be lowercase SHA-256 values")
    return decision
