from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from core.translation_discipline import discipline_route_codes

from .quality_decision import ACCEPTED_WITH_WARNINGS
from .quality_issue import canonical_issue_code

# Issues that may justify a warning but should not spend another provider call
# after deterministic/local normalization has already run.
_LOCAL_WARNING_CODES = {
    "NATURALNESS_GUARD",
    "SIMPLIFIED_CHINESE",
    "DIALOGUE_QUOTE_FORMAT",
    "PARAGRAPH_STRUCTURE_MERGED",
}

# These indicate potential content loss, hallucination, residue, or repetition.
# They must remain provider-blocking.
_PROVIDER_REQUIRED_CODES = {
    "EMPTY_OUTPUT",
    "TOO_SHORT",
    "PARAGRAPH_OMISSION_SUSPECTED",
    "SENTENCE_OMISSION_SUSPECTED",
    "HANGUL_RESIDUE",
    "DUPLICATE_LINE",
    "DUPLICATE_SENTENCE",
    "DUPLICATE_PARAGRAPH",
    "SEMANTIC_DUPLICATE_PARAGRAPH",
    "LOCKED_TERM_MISSING",
    "QUALITY_LOCK_VIOLATION",
}


def _codes(report: Mapping[str, Any]) -> set[str]:
    return {
        canonical_issue_code(issue.get("code"))
        for issue in report.get("merged_issues") or []
        if isinstance(issue, Mapping)
    }


def apply_smart_local_repair_decision(
    runtime_qa: Mapping[str, Any],
    *,
    local_repairs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Avoid provider retries for local-only/naturalness-only issues.

    This function never edits semantic content. The runtime has already applied
    deterministic normalization and locked-term repair before the unified gate.
    If the remaining blocking decision contains only local-warning issue codes,
    it is converted to ``accepted_with_warnings``. Fidelity/completeness,
    residue, terminology, and repetition problems remain retry-required.
    """
    result = deepcopy(dict(runtime_qa or {}))
    unified = deepcopy(dict(result.get("unified_quality_report") or {}))
    if not unified or unified.get("decision") != "retry_required":
        return result

    codes = _codes(unified)
    discipline_local = discipline_route_codes(unified, "local_repair")
    discipline_provider = discipline_route_codes(unified, "provider_retry")
    if discipline_local or discipline_provider:
        if not codes or discipline_provider:
            return result
        if codes != discipline_local:
            return result
    else:
        # Backward-compatible fallback for reports produced before TE v6.0 Stage 03.
        if not codes or codes & _PROVIDER_REQUIRED_CODES:
            return result
        if not codes.issubset(_LOCAL_WARNING_CODES):
            return result

    merged = []
    for issue in unified.get("merged_issues") or []:
        item = dict(issue)
        item["retry_required"] = False
        if str(item.get("severity") or "").lower() in {"critical", "high"}:
            item["severity"] = "medium"
        metadata = dict(item.get("metadata") or {})
        metadata["smart_local_repair_routing"] = "warning_without_provider_retry"
        item["metadata"] = metadata
        merged.append(item)

    unified.update({
        "merged_issues": merged,
        "decision": ACCEPTED_WITH_WARNINGS,
        "accepted": True,
        "passed": True,
        "retry_required": False,
        "final_reason": "Only locally handled or soft naturalness issues remain; provider retry was skipped.",
        "smart_local_repair": {
            "stage": "TE-v5.4.0",
            "provider_retry_skipped": True,
            "issue_codes": sorted(codes),
            "local_repairs": list(local_repairs or []),
        },
    })
    result.update({
        "passed": True,
        "status": ACCEPTED_WITH_WARNINGS,
        "decision": ACCEPTED_WITH_WARNINGS,
        "retry_required": False,
        "unified_quality_report": unified,
        "smart_local_repair": dict(unified["smart_local_repair"]),
    })
    for issue in result.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        if canonical_issue_code(issue.get("code")) in codes:
            issue["retry_worthy"] = False
            if str(issue.get("severity") or "").lower() == "error":
                issue["severity"] = "warning"
    return result
