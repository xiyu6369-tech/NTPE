from __future__ import annotations

from typing import Any, Mapping, Sequence


ACCEPTED = "accepted"
ACCEPTED_WITH_WARNINGS = "accepted_with_warnings"
RETRY_REQUIRED = "retry_required"
REJECTED = "rejected"
RUNTIME_ERROR = "runtime_error"

_PENALTIES = {
    "critical": 35,
    "high": 20,
    "medium": 10,
    "low": 4,
    "info": 1,
}


def calculate_unified_score(issues: Sequence[Mapping[str, Any]]) -> int:
    return max(0, 100 - sum(
        _PENALTIES.get(str(issue.get("severity") or "medium").lower(), 10)
        for issue in issues
    ))


def decide_quality(issues: Sequence[Mapping[str, Any]]) -> tuple[str, str]:
    if not issues:
        return ACCEPTED, "No merged quality issues were detected."
    severities = {str(issue.get("severity") or "medium").lower() for issue in issues}
    if any(bool(issue.get("rejected")) for issue in issues):
        return REJECTED, "At least one merged issue requires rejection."
    if severities & {"critical", "high"} or any(
        bool(issue.get("retry_required")) for issue in issues
    ):
        return RETRY_REQUIRED, "At least one merged issue requires another translation attempt."
    return ACCEPTED_WITH_WARNINGS, "Only non-blocking merged quality issues remain."
