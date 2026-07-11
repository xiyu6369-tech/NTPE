from __future__ import annotations

from typing import Any, Mapping, Optional

from .quality_repair_pipeline import QualityRepairPipeline
from .semantic_repetition import analyze_semantic_repetition
from .unified_quality_gate import build_runtime_qa_view, run_unified_quality_gate


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
    metrics = dict(baseline.get("metrics") or {})

    semantic_repetition = analyze_semantic_repetition(
        str(source_text or ""), normalized_text
    )
    issues.extend(semantic_repetition.get("issues") or [])
    metrics.update(semantic_repetition.get("metrics") or {})

    return {
        "stage": "TE-v5.3-phase1",
        "status": result.get("status", "unknown"),
        "accepted": bool(result.get("accepted")),
        "retry_required": bool((result.get("retry_result") or {}).get("retry")),
        "quality_score": int(quality.get("quality_score", 0) or 0),
        "normalized_text": normalized_text,
        "safe_replacements": safe_replacements,
        "issues": issues,
        "metrics": metrics,
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


def merge_quality_v5_into_runtime_qa(
    runtime_qa: Mapping[str, Any],
    report: Mapping[str, Any],
    *,
    attempt: int | None = None,
    chunk_id: str = "",
) -> dict[str, Any]:
    """Backward-compatible entry point backed by the v5.3.1 unified gate."""
    unified = run_unified_quality_gate(
        report or None,
        runtime_qa,
        attempt=attempt,
        chunk_id=chunk_id,
    )
    return build_runtime_qa_view(runtime_qa, unified, report or None)
