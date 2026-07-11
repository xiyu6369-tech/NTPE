from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from core.adaptive_context_runtime_shadow import ShadowAuditRecord, shadow_records
from .model import ProductionShadowValidationReport

VALIDATION_VERSION = "7.0.0-stage04"
DEFAULT_STAGE = "TE-v7.0-Stage04-ProductionShadowValidation"


def build_production_shadow_report(
    regression_result: dict[str, object], *,
    records: Iterable[ShadowAuditRecord] | None = None,
    provider_execution_requested: bool,
    stage: str = DEFAULT_STAGE,
) -> ProductionShadowValidationReport:
    rows = tuple(records if records is not None else shadow_records())
    equivalent = sum(1 for row in rows if row.payload_equivalent)
    mismatches = len(rows) - equivalent
    calls_added = sum(int(row.provider_calls_added) for row in rows)
    baseline_tokens = 0
    ace_tokens = 0
    admissible = 0
    fallback = 0
    latency_total = 0.0
    for row in rows:
        metrics = dict(row.metrics)
        baseline_tokens += int(metrics.get("baseline_context_tokens", 0) or 0)
        ace_tokens += int(metrics.get("ace_context_tokens", 0) or 0)
        admissible += int(bool(metrics.get("admissible", False)))
        fallback += int(bool(metrics.get("fallback_required", False)))
        latency_total += float(metrics.get("ace_build_latency_ms", 0.0) or 0.0)
    regression_status = str(regression_result.get("status", "unknown"))
    provider_observed = provider_execution_requested and regression_status != "dry_run"
    blockers: list[str] = []
    if regression_status not in {"success", "warning"}:
        blockers.append(f"regression-status:{regression_status}")
    if not rows:
        blockers.append("no-shadow-records")
    if mismatches:
        blockers.append(f"payload-mismatch:{mismatches}")
    if calls_added:
        blockers.append(f"shadow-provider-calls-added:{calls_added}")
    status = "pass" if not blockers else "fail"
    return ProductionShadowValidationReport(
        version=VALIDATION_VERSION,
        stage=stage,
        status=status,
        execution_mode="shadow",
        provider_execution_requested=provider_execution_requested,
        provider_execution_observed=provider_observed,
        shadow_records=len(rows),
        payload_equivalent_records=equivalent,
        payload_mismatch_records=mismatches,
        provider_calls_added=calls_added,
        admissible_records=admissible,
        fallback_records=fallback,
        baseline_context_tokens=baseline_tokens,
        ace_context_tokens=ace_tokens,
        estimated_tokens_saved=max(0, baseline_tokens - ace_tokens),
        ace_latency_total_ms=round(latency_total, 3),
        ace_latency_average_ms=round(latency_total / len(rows), 3) if rows else 0.0,
        regression_status=regression_status,
        blockers=tuple(blockers),
        metadata={
            "content_redacted": True,
            "prompt_payload_unchanged": mismatches == 0,
            "assembly_metrics_only": True,
            "translation_quality_improvement_claimed": False,
            "provider_latency_improvement_claimed": False,
        },
    )


def write_production_shadow_report(report: ProductionShadowValidationReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
