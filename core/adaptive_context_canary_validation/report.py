from __future__ import annotations
import json
from pathlib import Path
from core.adaptive_context_canary import canary_records
from .model import CanaryProductionValidationReport
from .stop import is_target_complete_result

VERSION = "7.0.0-stage06"

def _regression_status(result: dict[str, object]) -> str:
    return str(result.get("status", "unknown")).strip().lower() or "unknown"

def build_canary_production_report(
    regression_result: dict[str, object],
    *,
    target_chunk: int,
    provider_execution_requested: bool,
    stage: str,
) -> CanaryProductionValidationReport:
    rows = canary_records()
    attempted = tuple(row for row in rows if row.attempted)
    active = tuple(row for row in rows if row.activated)
    target_complete = is_target_complete_result(regression_result)
    provider_status = "target_chunk_complete" if target_complete else _regression_status(regression_result)
    blockers: list[str] = []
    limitations: list[str] = []
    fallback_reasons = tuple(dict.fromkeys(reason for row in attempted for reason in row.fallback_reasons))
    if len(active) > 1:
        blockers.append("multiple-canary-activations")
    if any(row.provider_calls_added for row in rows):
        blockers.append("provider-calls-added")
    if any(row.activated and row.payload_hash_before == row.payload_hash_after for row in rows):
        blockers.append("activated-payload-unchanged")
    if not rows:
        blockers.append("no-canary-records")
    if not attempted:
        blockers.append("target-chunk-not-observed")
    if attempted and not active:
        limitations.append("canary-not-activated")
        limitations.extend(f"canary-fallback:{reason}" for reason in fallback_reasons)
    regression_success = provider_status == "success" or target_complete
    if provider_execution_requested and not regression_success:
        limitations.append(f"provider-regression-status:{provider_status}")
    hard_safe = not blockers
    ready = hard_safe and bool(active) and provider_execution_requested and regression_success
    if ready:
        status = "pass"
    elif hard_safe and active and provider_execution_requested:
        status = "pass_with_external_provider_limitation"
    elif hard_safe and not provider_execution_requested:
        status = "pass_without_provider_activation"
    elif hard_safe and attempted and not active:
        status = "pass_without_canary_activation"
    else:
        status = "fail"
    total_latency = round(sum(row.latency_ms for row in rows), 3)
    return CanaryProductionValidationReport(
        version=VERSION,
        stage=stage,
        status=status,
        ready=ready,
        provider_status=provider_status,
        records=len(rows),
        attempted_records=len(attempted),
        activated_records=len(active),
        fallback_records=sum(1 for row in attempted if row.fallback_used),
        target_chunk=max(1, int(target_chunk)),
        baseline_context_tokens=sum(row.baseline_context_tokens for row in attempted),
        canary_context_tokens=sum(row.canary_context_tokens for row in attempted),
        estimated_tokens_saved=sum(row.estimated_tokens_saved for row in active),
        payload_changed_records=sum(1 for row in active if row.payload_hash_before != row.payload_hash_after),
        provider_calls_added=sum(row.provider_calls_added for row in rows),
        fallback_reasons=fallback_reasons,
        target_chunk_completed=target_complete,
        canary_latency_total_ms=total_latency,
        canary_latency_average_ms=round(total_latency / len(rows), 3) if rows else 0.0,
        blockers=tuple(blockers),
        limitations=tuple(limitations),
        metadata={
            "content_redacted": True,
            "single_chunk_only": True,
            "automatic_expansion": False,
            "target_chunk_stop_enabled": True,
            "provider_timeout_is_not_ace_failure": True,
            "translation_quality_improvement_claimed": False,
            "provider_latency_improvement_claimed": False,
        },
    )

def write_canary_production_report(report: CanaryProductionValidationReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
