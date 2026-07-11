from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .quality_adapter import UnifiedQualityGateAdapter

QUALITY_ENFORCEMENT_VERSION = "6.0.0-stage03"

_LOCAL_REPAIR_CODES = frozenset({
    "NATURALNESS_GUARD",
    "SIMPLIFIED_CHINESE",
    "DIALOGUE_QUOTE_FORMAT",
    "PARAGRAPH_STRUCTURE_MERGED",
})

_PROVIDER_RETRY_CODES = frozenset({
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
    "HALLUCINATION",
    "ADDED_DETAIL",
})


def _canonical_code(value: Any) -> str:
    code = str(value or "").strip().upper()
    return code[3:] if code.startswith("V5_") else code


def _route_for_issue(issue: Mapping[str, Any]) -> str:
    code = _canonical_code(issue.get("code") or issue.get("type"))
    if code in _LOCAL_REPAIR_CODES:
        return "local_repair"
    if code in _PROVIDER_RETRY_CODES or bool(issue.get("retry_required")):
        return "provider_retry"
    severity = str(issue.get("severity") or "").strip().lower()
    if severity in {"critical", "high"}:
        return "provider_retry"
    return "warning"


class DisciplineQualityEnforcer:
    """Annotate quality reports with discipline policy routing.

    Stage 03 is deliberately non-destructive: score, decision, accepted and
    retry_required remain untouched. The annotations become the canonical
    source for downstream routing while preserving v5 behavior exactly.
    """

    def __init__(self, quality_adapter: UnifiedQualityGateAdapter) -> None:
        self.quality_adapter = quality_adapter

    def enforce(self, report: Mapping[str, Any]) -> dict[str, Any]:
        adapted = self.quality_adapter.adapt(report)
        result = deepcopy(adapted)
        mappings = dict(result.get("discipline_issue_mappings") or {})
        annotated: list[dict[str, Any]] = []
        route_counts = {"local_repair": 0, "provider_retry": 0, "warning": 0}

        for raw in result.get("merged_issues") or []:
            if not isinstance(raw, Mapping):
                continue
            issue = dict(raw)
            code = _canonical_code(issue.get("code") or issue.get("type"))
            route = _route_for_issue(issue)
            route_counts[route] += 1
            metadata = dict(issue.get("metadata") or {})
            metadata.update({
                "discipline_quality_enforcement_version": QUALITY_ENFORCEMENT_VERSION,
                "discipline_rule_code": mappings.get(code),
                "discipline_route": route,
                "discipline_policy_enforced": True,
            })
            issue["metadata"] = metadata
            annotated.append(issue)

        result["merged_issues"] = annotated
        result["discipline_quality_enforcement"] = {
            "version": QUALITY_ENFORCEMENT_VERSION,
            "enabled": True,
            "decision_preserved": True,
            "score_preserved": True,
            "route_counts": route_counts,
            "local_repair_issue_codes": sorted(
                _canonical_code(item.get("code"))
                for item in annotated
                if (item.get("metadata") or {}).get("discipline_route") == "local_repair"
            ),
            "provider_retry_issue_codes": sorted(
                _canonical_code(item.get("code"))
                for item in annotated
                if (item.get("metadata") or {}).get("discipline_route") == "provider_retry"
            ),
            "warning_issue_codes": sorted(
                _canonical_code(item.get("code"))
                for item in annotated
                if (item.get("metadata") or {}).get("discipline_route") == "warning"
            ),
        }
        return result


def discipline_route_codes(report: Mapping[str, Any], route: str) -> set[str]:
    return {
        _canonical_code(issue.get("code") or issue.get("type"))
        for issue in report.get("merged_issues") or []
        if isinstance(issue, Mapping)
        and (issue.get("metadata") or {}).get("discipline_route") == route
    }
