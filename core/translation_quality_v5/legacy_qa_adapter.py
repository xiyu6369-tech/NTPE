from __future__ import annotations

from typing import Any, Mapping

from .quality_issue import (
    UnifiedQualityIssue,
    canonical_issue_code,
    category_for_code,
    normalize_severity,
)


def adapt_legacy_qa_report(report: Mapping[str, Any] | None) -> list[UnifiedQualityIssue]:
    """Normalize Legacy Runtime QA output without copying its detection rules."""
    legacy = dict(report or {})
    legacy_passed = bool(legacy.get("passed", True))
    normalized: list[UnifiedQualityIssue] = []
    for raw in legacy.get("issues") or []:
        if not isinstance(raw, Mapping):
            continue
        code = canonical_issue_code(raw.get("code") or raw.get("type"))
        default_severity = "medium" if legacy_passed else "high"
        severity = normalize_severity(raw.get("severity"), default=default_severity)
        evidence = raw.get("evidence")
        if evidence is None:
            evidence = raw.get("samples", raw.get("sample", {}))
        metadata = {
            key: value for key, value in raw.items()
            if key not in {
                "code", "type", "category", "severity", "message",
                "evidence", "samples", "sample", "retry_worthy",
            }
        }
        metadata["original_code"] = str(raw.get("code") or raw.get("type") or "")
        normalized.append(UnifiedQualityIssue(
            code=code,
            category=str(raw.get("category") or category_for_code(code)),
            severity=severity,
            message=str(raw.get("message") or code),
            evidence=evidence,
            source="legacy_runtime_qa",
            repairable=bool(raw.get("repairable", False)),
            retry_required=bool(raw.get("retry_worthy")) or severity in {"critical", "high"},
            metadata=metadata,
        ))
    return normalized
