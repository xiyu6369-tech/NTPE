from __future__ import annotations

from typing import Any, Mapping, Sequence

from core.translation_discipline import DisciplineQualityEnforcer, TranslationDisciplineEngine
from core.translation_discipline.quality_adapter import UnifiedQualityGateAdapter

from .legacy_qa_adapter import adapt_legacy_qa_report
from .quality_decision import (
    ACCEPTED,
    ACCEPTED_WITH_WARNINGS,
    calculate_unified_score,
    decide_quality,
)
from .quality_issue import (
    UnifiedQualityIssue,
    canonical_issue_code,
    normalize_severity,
    quality_v5_issue_to_unified,
)


_SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _merge_evidence(first: Any, second: Any) -> Any:
    if not first:
        return second
    if not second or second == first:
        return first
    values: list[Any] = []
    for value in (first, second):
        if isinstance(value, list):
            for item in value:
                if item not in values:
                    values.append(item)
        elif value not in values:
            values.append(value)
    return values


def deduplicate_issues(issues: Sequence[UnifiedQualityIssue]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for issue in issues:
        item = issue.to_dict()
        key = item["code"]
        if key not in merged:
            item["metadata"] = dict(item.get("metadata") or {})
            item["metadata"]["sources"] = [item["source"]]
            merged[key] = item
            order.append(key)
            continue
        current = merged[key]
        current_severity = normalize_severity(current.get("severity"))
        new_severity = normalize_severity(item.get("severity"))
        if _SEVERITY_RANK[new_severity] > _SEVERITY_RANK[current_severity]:
            current["severity"] = new_severity
            current["message"] = item["message"]
        current["evidence"] = _merge_evidence(current.get("evidence"), item.get("evidence"))
        current["repairable"] = bool(current.get("repairable")) or bool(item.get("repairable"))
        current["retry_required"] = bool(current.get("retry_required")) or bool(item.get("retry_required"))
        sources = current.setdefault("metadata", {}).setdefault("sources", [])
        if item["source"] not in sources:
            sources.append(item["source"])
        current["source"] = "+".join(sources)
    return [merged[key] for key in order]


def run_unified_quality_gate(
    quality_v5_report: Mapping[str, Any] | None,
    legacy_qa_report: Mapping[str, Any] | None,
    *,
    attempt: int | None = None,
    chunk_id: str = "",
) -> dict[str, Any]:
    quality_report = dict(quality_v5_report or {})
    v5_retry = bool(quality_report.get("retry_required"))
    v5_issues = [
        quality_v5_issue_to_unified(issue, report_retry_required=v5_retry)
        for issue in quality_report.get("issues") or []
        if isinstance(issue, Mapping)
    ]
    legacy_issues = adapt_legacy_qa_report(legacy_qa_report)
    if quality_v5_report and not quality_report.get("accepted", True) and not v5_issues:
        v5_issues.append(UnifiedQualityIssue(
            code="QUALITY_V5_GATE_REJECTED",
            category="quality",
            severity="high",
            message="TE v5 rejected the output without a detailed baseline issue.",
            source="translation_quality_v5",
            retry_required=True,
            metadata={"status": quality_report.get("status")},
        ))
    if legacy_qa_report and not (legacy_qa_report or {}).get("passed", True) and not legacy_issues:
        legacy_issues.append(UnifiedQualityIssue(
            code="LEGACY_QA_FAILED",
            category="quality",
            severity="high",
            message="Legacy Runtime QA failed without a detailed issue.",
            source="legacy_runtime_qa",
            retry_required=True,
        ))
    merged_issues = deduplicate_issues([*v5_issues, *legacy_issues])
    score = calculate_unified_score(merged_issues)
    decision, final_reason = decide_quality(merged_issues)
    base_report = {
        "schema_version": "5.3.1",
        "stage": "TE-v5.3.1-unified-quality-gate",
        "quality_v5_issues": [issue.to_dict() for issue in v5_issues],
        "legacy_qa_issues": [issue.to_dict() for issue in legacy_issues],
        "merged_issues": merged_issues,
        "normalizations": list(quality_report.get("safe_replacements") or []),
        "score": score,
        "decision": decision,
        "accepted": decision in {ACCEPTED, ACCEPTED_WITH_WARNINGS},
        "passed": decision in {ACCEPTED, ACCEPTED_WITH_WARNINGS},
        "retry_required": decision == "retry_required",
        "final_reason": final_reason,
        "attempt": attempt,
        "chunk_id": chunk_id,
        "quality_v5_enabled": bool(quality_v5_report),
        "legacy_qa_enabled": bool((legacy_qa_report or {}).get("enabled", True)),
    }
    discipline = TranslationDisciplineEngine(profile="literary")
    enforcer = DisciplineQualityEnforcer(UnifiedQualityGateAdapter(discipline.feedback))
    return enforcer.enforce(base_report)


def build_runtime_qa_view(
    legacy_qa_report: Mapping[str, Any] | None,
    unified_report: Mapping[str, Any],
    quality_v5_report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    runtime = dict(legacy_qa_report or {})
    compatibility_issues = [
        dict(issue) for issue in (legacy_qa_report or {}).get("issues") or []
        if isinstance(issue, Mapping)
    ]
    legacy_codes = {
        canonical_issue_code(issue.get("code") or issue.get("type"))
        for issue in compatibility_issues
    }
    for issue in unified_report.get("merged_issues") or []:
        item = dict(issue)
        sources = list((item.get("metadata") or {}).get("sources") or [])
        if "legacy_runtime_qa" in sources or item.get("code") in legacy_codes:
            continue
        item["code"] = f"V5_{item['code']}"
        evidence = item.get("evidence")
        if evidence:
            item["samples"] = evidence if isinstance(evidence, list) else [evidence]
        item["retry_worthy"] = bool(item.get("retry_required"))
        compatibility_issues.append(item)
    runtime.update({
        "passed": bool(unified_report.get("passed")),
        "status": unified_report.get("decision"),
        "decision": unified_report.get("decision"),
        "score": unified_report.get("score"),
        "issues": compatibility_issues,
        "retry_required": bool(unified_report.get("retry_required")),
        "unified_quality_report": dict(unified_report),
        "quality_v5": {
            "stage": (quality_v5_report or {}).get("stage"),
            "status": (quality_v5_report or {}).get("status"),
            "accepted": (quality_v5_report or {}).get("accepted"),
            "retry_required": (quality_v5_report or {}).get("retry_required"),
            "quality_score": (quality_v5_report or {}).get("quality_score"),
            "safe_replacements": (quality_v5_report or {}).get("safe_replacements", []),
        },
    })
    return runtime


def attach_unified_report(
    quality_v5_report: Mapping[str, Any],
    unified_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Add v5.3.1 fields while preserving every Phase 1 report field."""
    report = dict(quality_v5_report)
    report.update({
        key: unified_report.get(key) for key in (
            "schema_version", "quality_v5_issues", "legacy_qa_issues",
            "merged_issues", "normalizations", "score", "decision",
            "retry_required", "final_reason", "attempt", "chunk_id",
        )
    })
    report["unified_stage"] = unified_report.get("stage")
    report["unified_accepted"] = unified_report.get("accepted")
    return report
