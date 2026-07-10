from __future__ import annotations

from typing import Any, Mapping, Optional

from .quality_repair_pipeline import QualityRepairPipeline


_PHASE1_SAFE_REPLACEMENTS = {
    "一周": "一週",
    "本周": "本週",
    "上周": "上週",
    "下周": "下週",
    "每周": "每週",
    "周末": "週末",
}


def _safe_phase1_normalize(text: str) -> tuple[str, list[dict[str, str]]]:
    normalized = text
    replacements: list[dict[str, str]] = []
    for source, target in _PHASE1_SAFE_REPLACEMENTS.items():
        if source in normalized:
            count = normalized.count(source)
            normalized = normalized.replace(source, target)
            replacements.append({"from": source, "to": target, "count": str(count)})
    return normalized, replacements


def run_quality_v5_phase1(
    source_text: Optional[str],
    translated_text: Optional[str],
    *,
    locked_terms: Optional[Mapping[str, str]] = None,
    config: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Run TE-v5 quality analysis with conservative runtime-safe repairs only.

    Phase 1 never rewrites semantics and never calls a provider. It applies
    Unicode/Traditional-Chinese normalization, known terminology aliases, and
    a small set of unambiguous Traditional-Chinese orthography repairs.
    """
    pipeline = QualityRepairPipeline()
    result = pipeline.run(
        source_text,
        translated_text,
        locked_terms=locked_terms or {},
        runtime_state={"scope": "single_chunk", "phase": "TE-v5.3-phase1"},
        config=config or {},
    )
    normalized_text, safe_replacements = _safe_phase1_normalize(
        str(result.get("normalized_text") or translated_text or "")
    )
    quality = dict(result.get("quality_result") or {})
    baseline = dict(quality.get("baseline_report") or {})
    issues = list(baseline.get("issues") or [])

    return {
        "stage": "TE-v5.3-phase1",
        "status": result.get("status", "unknown"),
        "accepted": bool(result.get("accepted")),
        "retry_required": bool((result.get("retry_result") or {}).get("retry")),
        "quality_score": int(quality.get("quality_score", 0) or 0),
        "normalized_text": normalized_text,
        "safe_replacements": safe_replacements,
        "issues": issues,
        "metrics": dict(baseline.get("metrics") or {}),
        "repair_actions": list(quality.get("repair_actions") or []),
        "quality_result": quality,
        "repair_plan": result.get("repair_plan") or {},
        "retry_result": result.get("retry_result") or {},
        "rebuild_result": result.get("rebuild_result") or {},
        "runtime_integration": {
            "enabled": True,
            "mode": "conservative_phase1",
            "provider_called": False,
            "semantic_rewrite_allowed": False,
            "safe_text_replacement_allowed": True,
        },
    }


def merge_quality_v5_into_runtime_qa(runtime_qa: Mapping[str, Any], report: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(runtime_qa or {})
    existing = list(merged.get("issues") or [])
    seen = {str(item.get("code")) for item in existing if isinstance(item, Mapping)}
    for issue in report.get("issues") or []:
        if not isinstance(issue, Mapping):
            continue
        code = f"V5_{str(issue.get('code') or 'QUALITY_ISSUE').upper()}"
        if code in seen:
            continue
        existing.append({
            "code": code,
            "severity": issue.get("severity", "medium"),
            "message": issue.get("message", code),
            "repair_action": issue.get("repair_action", "quality_review"),
            "details": issue.get("details", {}),
            "source": "translation_quality_v5",
        })
        seen.add(code)

    merged["issues"] = existing
    merged["quality_v5"] = {
        "stage": report.get("stage"),
        "status": report.get("status"),
        "accepted": report.get("accepted"),
        "retry_required": report.get("retry_required"),
        "quality_score": report.get("quality_score"),
        "safe_replacements": report.get("safe_replacements", []),
    }
    blocking = any(
        str(item.get("severity", "")).lower() in {"critical", "high"}
        for item in existing if isinstance(item, Mapping) and item.get("source") == "translation_quality_v5"
    )
    merged["passed"] = bool(merged.get("passed", True)) and not blocking
    if blocking:
        merged["status"] = "fail"
    return merged
