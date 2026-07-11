from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

BEST_ATTEMPT_VERSION = "5.5.3.2"

_DECISION_RANK = {
    "accepted": 5,
    "accepted_with_warnings": 4,
    "retry_required": 2,
    "rejected": 1,
    "runtime_error": 0,
}


@dataclass(frozen=True)
class AttemptCandidate:
    qa_attempt: int
    translation: str
    qa_report: Mapping[str, Any]
    quality_v5_report: Mapping[str, Any] | None
    result: Mapping[str, Any]

    @property
    def unified(self) -> Mapping[str, Any]:
        value = self.qa_report.get("unified_quality_report")
        return value if isinstance(value, Mapping) else {}

    def rank(self) -> tuple[int, int, int, int, int]:
        decision = str(self.unified.get("decision") or self.qa_report.get("decision") or "runtime_error")
        score = int(self.unified.get("score") or self.qa_report.get("score") or 0)
        issues = self.unified.get("merged_issues") or self.qa_report.get("issues") or []
        blocking = sum(
            1 for issue in issues
            if isinstance(issue, Mapping)
            and (
                bool(issue.get("retry_required") or issue.get("retry_worthy"))
                or str(issue.get("severity") or "").lower() in {"critical", "high"}
            )
        )
        issue_count = len([issue for issue in issues if isinstance(issue, Mapping)])
        return (
            _DECISION_RANK.get(decision, 0),
            score,
            -blocking,
            -issue_count,
            len(self.translation.strip()),
        )


def select_best_attempt(candidates: Sequence[AttemptCandidate]) -> AttemptCandidate | None:
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate.rank())


def classify_provider_error(error: str) -> str:
    value = str(error or "").lower()
    if "timeout" in value:
        return "provider_timeout"
    if "503" in value or "resourceexhausted" in value or "service unavailable" in value:
        return "provider_capacity"
    if "429" in value or "rate limit" in value or "too many requests" in value:
        return "provider_rate_limit"
    return "provider_error"


def selection_metadata(
    candidates: Sequence[AttemptCandidate],
    selected: AttemptCandidate,
    *,
    selection_reason: str | None = None,
    later_provider_error: str | None = None,
    later_qa_attempt: int | None = None,
) -> dict[str, Any]:
    metadata = {
        "version": BEST_ATTEMPT_VERSION,
        "selected_qa_attempt": selected.qa_attempt,
        "candidate_count": len(candidates),
        "candidates": [
            {
                "qa_attempt": item.qa_attempt,
                "decision": item.unified.get("decision") or item.qa_report.get("decision"),
                "score": item.unified.get("score") or item.qa_report.get("score"),
                "blocking_issue_count": -item.rank()[2],
                "issue_count": -item.rank()[3],
            }
            for item in candidates
        ],
    }
    if selection_reason:
        metadata["selection_reason"] = selection_reason
    if later_provider_error:
        metadata["later_error_type"] = classify_provider_error(later_provider_error)
        metadata["later_error"] = str(later_provider_error)[:500]
    if later_qa_attempt is not None:
        metadata["later_qa_attempt"] = int(later_qa_attempt)
    return metadata
