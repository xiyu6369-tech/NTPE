from __future__ import annotations

from enum import Enum


class ReviewDecisionStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


ALLOWED_DECISIONS = tuple(status.value for status in ReviewDecisionStatus)

