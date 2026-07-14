from __future__ import annotations

from enum import Enum


class CorpusLifecycle(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


ALLOWED_TRANSITIONS = {
    CorpusLifecycle.DRAFT: frozenset({CorpusLifecycle.UNDER_REVIEW, CorpusLifecycle.REJECTED}),
    CorpusLifecycle.UNDER_REVIEW: frozenset({CorpusLifecycle.APPROVED, CorpusLifecycle.REJECTED, CorpusLifecycle.DRAFT}),
    CorpusLifecycle.APPROVED: frozenset({CorpusLifecycle.SUPERSEDED, CorpusLifecycle.DEPRECATED}),
    CorpusLifecycle.SUPERSEDED: frozenset({CorpusLifecycle.DEPRECATED}),
    CorpusLifecycle.DEPRECATED: frozenset(),
    CorpusLifecycle.REJECTED: frozenset(),
}


def validate_lifecycle_transition(current: CorpusLifecycle | str, target: CorpusLifecycle | str) -> bool:
    try:
        source = current if isinstance(current, CorpusLifecycle) else CorpusLifecycle(current)
        destination = target if isinstance(target, CorpusLifecycle) else CorpusLifecycle(target)
    except ValueError as exc:
        raise ValueError("unknown corpus lifecycle status") from exc
    if destination not in ALLOWED_TRANSITIONS[source]:
        raise ValueError(f"invalid corpus lifecycle transition: {source.value} -> {destination.value}")
    return True

