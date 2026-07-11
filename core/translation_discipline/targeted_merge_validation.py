from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

from .targeted_retry_plan import TargetedRetryUnit

TARGETED_MERGE_VALIDATION_VERSION = "6.0.0-stage11.4"


def _norm(text: str) -> str:
    return re.sub(r"[\s\W_]+", "", str(text or "")).lower()


def _ngrams(text: str, n: int = 2) -> set[str]:
    value = _norm(text)
    if len(value) < n:
        return {value} if value else set()
    return {value[i:i+n] for i in range(len(value) - n + 1)}


def _overlap(a: str, b: str) -> float:
    left, right = _ngrams(a), _ngrams(b)
    if not left or not right:
        return 0.0
    return len(left & right) / max(1, min(len(left), len(right)))


@dataclass(frozen=True)
class TargetedMergeValidationResult:
    accepted: bool
    reason: str
    checks: Mapping[str, bool] = field(default_factory=dict)
    metrics: Mapping[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": TARGETED_MERGE_VALIDATION_VERSION,
            "accepted": self.accepted,
            "reason": self.reason,
            "checks": dict(self.checks),
            "metrics": dict(self.metrics),
            "fail_closed": True,
        }


def validate_targeted_merge(
    original_text: str,
    replacement: str,
    merged_text: str,
    unit: TargetedRetryUnit,
    *,
    boundary_window: int = 120,
    duplicate_threshold: float = 0.82,
) -> TargetedMergeValidationResult:
    metadata = dict(unit.metadata)
    start, end = metadata.get("translated_start"), metadata.get("translated_end")
    if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int):
        return TargetedMergeValidationResult(False, "missing_translated_range", {"range_valid": False})
    range_valid = 0 <= start <= end <= len(original_text)
    if not range_valid:
        return TargetedMergeValidationResult(False, "invalid_translated_range", {"range_valid": False})

    replacement_clean = str(replacement or "").strip()
    nonempty = bool(_norm(replacement_clean))
    prefix_preserved = merged_text[:start] == original_text[:start]
    suffix_preserved = merged_text[start + len(str(metadata.get("merge_separator") or "")) + len(str(replacement)):] == original_text[end:]

    left_context = original_text[max(0, start - boundary_window):start]
    right_context = original_text[end:end + boundary_window]
    left_dup = _overlap(left_context, replacement_clean)
    right_dup = _overlap(replacement_clean, right_context)
    boundary_duplicate = max(left_dup, right_dup) >= duplicate_threshold

    source_len = max(1, unit.source_end - unit.source_start)
    replacement_ratio = len(_norm(replacement_clean)) / source_len
    plausible_length = 0.15 <= replacement_ratio <= 3.5

    checks = {
        "range_valid": range_valid,
        "replacement_nonempty": nonempty,
        "prefix_preserved": prefix_preserved,
        "suffix_preserved": suffix_preserved,
        "no_boundary_duplicate": not boundary_duplicate,
        "plausible_replacement_length": plausible_length,
    }
    accepted = all(checks.values())
    reason = "accepted" if accepted else next((name for name, ok in checks.items() if not ok), "rejected")
    return TargetedMergeValidationResult(
        accepted,
        reason,
        checks,
        {
            "translated_start": start,
            "translated_end": end,
            "source_length": source_len,
            "replacement_length": len(_norm(replacement_clean)),
            "replacement_length_ratio": round(replacement_ratio, 4),
            "left_boundary_overlap": round(left_dup, 4),
            "right_boundary_overlap": round(right_dup, 4),
        },
    )
