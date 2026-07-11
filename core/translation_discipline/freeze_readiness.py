from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json

from .production_comparison import compare_stage_outputs, summarize_retry_metrics

FREEZE_READINESS_VERSION = "6.0.0-stage10.3"

@dataclass
class FreezeReadinessResult:
    version: str = FREEZE_READINESS_VERSION
    ready: bool = False
    expected_chunks: int = 0
    observed_chunks: int = 0
    accepted_chunks: int = 0
    blocking_chunks: int = 0
    comparison_complete: bool = False
    provider_budget_accounted: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    comparison: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_freeze_readiness(
    baseline_dir: str | Path,
    current_dir: str | Path,
    *,
    expected_chunks: int,
) -> FreezeReadinessResult:
    metrics = summarize_retry_metrics(current_dir)
    comparison = compare_stage_outputs(baseline_dir, current_dir)
    accepted = metrics.accepted + metrics.accepted_with_warnings
    blocking = metrics.provider_retry + metrics.rejected
    result = FreezeReadinessResult(
        expected_chunks=max(0, int(expected_chunks)),
        observed_chunks=metrics.chunks_observed,
        accepted_chunks=accepted,
        blocking_chunks=blocking,
        comparison_complete=(comparison.baseline.chunks_observed > 0 and comparison.current.chunks_observed > 0),
        provider_budget_accounted=(metrics.recovery_budget_used <= metrics.recovery_budget_limit),
        metrics=metrics.to_dict(),
        comparison=comparison.to_dict(),
    )
    if result.expected_chunks <= 0:
        result.blockers.append("expected_chunks must be greater than zero")
    if result.observed_chunks != result.expected_chunks:
        result.blockers.append(
            f"Golden Set incomplete: observed {result.observed_chunks}/{result.expected_chunks} chunks"
        )
    if result.accepted_chunks != result.expected_chunks:
        result.blockers.append(
            f"Not all chunks accepted: accepted {result.accepted_chunks}/{result.expected_chunks}"
        )
    if result.blocking_chunks:
        result.blockers.append(f"Blocking final decisions remain: {result.blocking_chunks}")
    if not result.comparison_complete:
        result.blockers.append("Baseline/current comparison is incomplete")
    if not result.provider_budget_accounted:
        result.blockers.append("Provider recovery budget accounting is inconsistent")
    if metrics.source_kind != "discipline_audit":
        result.blockers.append("Current production evidence must use discipline audit reports")
    if metrics.warnings:
        result.warnings.extend(metrics.warnings)
    result.ready = not result.blockers
    return result


def write_freeze_readiness_report(
    baseline_dir: str | Path,
    current_dir: str | Path,
    output_path: str | Path,
    *,
    expected_chunks: int,
) -> dict[str, Any]:
    result = evaluate_freeze_readiness(
        baseline_dir,
        current_dir,
        expected_chunks=expected_chunks,
    ).to_dict()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
