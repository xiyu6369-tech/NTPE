from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .review_status import ReviewDecisionStatus


@dataclass(frozen=True)
class ReviewerProvenance:
    reviewer_id: str
    display_name: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class HumanReviewDecision:
    decision_id: str
    review_id: str
    decision: ReviewDecisionStatus
    decision_source: str
    reviewer: ReviewerProvenance
    schema_version: str
    created_at: str
    decision_reason: str
    review_artifact_sha256: str
    metrics_sha256: str
    defects_sha256: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decision"] = self.decision.value
        return payload

