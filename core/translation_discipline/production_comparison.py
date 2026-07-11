from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
import json
import re

PRODUCTION_COMPARISON_VERSION = "6.0.0-stage10.2"
_AUDIT_RE = re.compile(r"_chunk_(\d+)_discipline_audit_attempt_(\d+)\.json$")
_QUALITY_RE = re.compile(r"_chunk_(\d+)_quality_v5_attempt_(\d+)\.json$")


@dataclass
class StageRetryMetrics:
    version: str = PRODUCTION_COMPARISON_VERSION
    stage_dir: str = ""
    source_kind: str = "none"
    chunks_observed: int = 0
    qa_attempts: int = 0
    accepted: int = 0
    accepted_with_warnings: int = 0
    provider_retry: int = 0
    targeted_retry: int = 0
    full_retry: int = 0
    local_repair: int = 0
    rejected: int = 0
    recovery_budget_limit: int = 0
    recovery_budget_used: int = 0
    recovery_budget_remaining: int = 0
    issue_codes: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def retry_rate(self) -> float:
        return round(self.provider_retry / self.chunks_observed, 4) if self.chunks_observed else 0.0

    @property
    def accepted_rate(self) -> float:
        accepted = self.accepted + self.accepted_with_warnings
        return round(accepted / self.chunks_observed, 4) if self.chunks_observed else 0.0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["retry_rate"] = self.retry_rate
        payload["accepted_rate"] = self.accepted_rate
        payload["issue_codes"] = dict(sorted(self.issue_codes.items()))
        return payload


@dataclass
class ProductionComparison:
    version: str
    baseline: StageRetryMetrics
    current: StageRetryMetrics
    delta: dict[str, Any]
    interpretation: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "baseline": self.baseline.to_dict(),
            "current": self.current.to_dict(),
            "delta": dict(self.delta),
            "interpretation": list(self.interpretation),
        }


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _latest_by_chunk(paths: Iterable[Path], pattern: re.Pattern[str]) -> tuple[dict[int, tuple[int, Path]], int]:
    latest: dict[int, tuple[int, Path]] = {}
    attempts = 0
    for path in paths:
        match = pattern.search(path.name)
        if not match:
            continue
        attempts += 1
        chunk_index, attempt = int(match.group(1)), int(match.group(2))
        previous = latest.get(chunk_index)
        if previous is None or attempt > previous[0]:
            latest[chunk_index] = (attempt, path)
    return latest, attempts


def _add_issue_codes(metrics: StageRetryMetrics, issues: Iterable[Any]) -> None:
    for issue in issues:
        if isinstance(issue, dict):
            code = str(issue.get("code") or issue.get("type") or "UNKNOWN")
        else:
            code = str(issue or "UNKNOWN")
        metrics.issue_codes[code] = metrics.issue_codes.get(code, 0) + 1


def _summarize_audits(root: Path) -> StageRetryMetrics | None:
    paths = list(root.rglob("*_discipline_audit_attempt_*.json"))
    latest, attempts = _latest_by_chunk(paths, _AUDIT_RE)
    if not latest:
        return None
    metrics = StageRetryMetrics(stage_dir=str(root), source_kind="discipline_audit", qa_attempts=attempts)
    metrics.chunks_observed = len(latest)
    for _, path in sorted(latest.values(), key=lambda item: item[1].name):
        payload = _read_json(path)
        if payload is None:
            metrics.warnings.append(f"Unreadable audit report: {path}")
            continue
        action = str(payload.get("final_action") or "")
        if action == "accept":
            metrics.accepted += 1
        elif action == "accept_with_warnings":
            metrics.accepted_with_warnings += 1
        elif action == "provider_retry":
            metrics.provider_retry += 1
        elif action == "reject":
            metrics.rejected += 1

        policy = dict(payload.get("adaptive_retry_policy") or {})
        tier = str(policy.get("retry_tier") or policy.get("tier") or "")
        if tier == "targeted_retry":
            metrics.targeted_retry += 1
        elif tier == "full_retry":
            metrics.full_retry += 1

        repair = dict(payload.get("local_repair") or {})
        if bool(repair.get("changed")):
            metrics.local_repair += 1

        budget = dict(policy.get("provider_call_budget") or {})
        metrics.recovery_budget_limit += int(budget.get("limit") or 0)
        metrics.recovery_budget_used += int(budget.get("used") or 0)
        metrics.recovery_budget_remaining += int(budget.get("remaining") or 0)
        _add_issue_codes(metrics, (payload.get("quality") or {}).get("issues") or [])
    return metrics


def _summarize_quality_reports(root: Path) -> StageRetryMetrics | None:
    paths = list(root.rglob("*_quality_v5_attempt_*.json"))
    latest, attempts = _latest_by_chunk(paths, _QUALITY_RE)
    if not latest:
        return None
    metrics = StageRetryMetrics(stage_dir=str(root), source_kind="quality_v5", qa_attempts=attempts)
    metrics.chunks_observed = len(latest)
    for _, path in sorted(latest.values(), key=lambda item: item[1].name):
        payload = _read_json(path)
        if payload is None:
            metrics.warnings.append(f"Unreadable quality report: {path}")
            continue
        status = str(payload.get("decision") or payload.get("status") or "")
        retry_required = bool(payload.get("retry_required")) or status in {"retry_required", "rejected"}
        accepted = bool(payload.get("accepted"))
        issues = payload.get("merged_issues") or payload.get("issues") or []
        if retry_required:
            metrics.provider_retry += 1
        elif accepted and issues:
            metrics.accepted_with_warnings += 1
        elif accepted or status in {"accepted", "quality_pass"}:
            metrics.accepted += 1
        else:
            metrics.rejected += 1
        _add_issue_codes(metrics, issues)
    metrics.warnings.append("Legacy baseline lacks Stage 10 retry-tier and recovery-budget metadata.")
    return metrics


def summarize_retry_metrics(stage_dir: str | Path) -> StageRetryMetrics:
    root = Path(stage_dir)
    metrics = _summarize_audits(root) or _summarize_quality_reports(root)
    if metrics is not None:
        return metrics
    return StageRetryMetrics(stage_dir=str(root), warnings=["No audit or quality-v5 reports found."])


def compare_stage_outputs(baseline_dir: str | Path, current_dir: str | Path) -> ProductionComparison:
    baseline = summarize_retry_metrics(baseline_dir)
    current = summarize_retry_metrics(current_dir)
    delta = {
        "chunks_observed": current.chunks_observed - baseline.chunks_observed,
        "qa_attempts": current.qa_attempts - baseline.qa_attempts,
        "provider_retry": current.provider_retry - baseline.provider_retry,
        "targeted_retry": current.targeted_retry - baseline.targeted_retry,
        "full_retry": current.full_retry - baseline.full_retry,
        "local_repair": current.local_repair - baseline.local_repair,
        "recovery_budget_used": current.recovery_budget_used - baseline.recovery_budget_used,
        "retry_rate": round(current.retry_rate - baseline.retry_rate, 4),
        "accepted_rate": round(current.accepted_rate - baseline.accepted_rate, 4),
    }
    interpretation: list[str] = []
    if current.provider_retry < baseline.provider_retry:
        interpretation.append("Current stage required fewer final Provider-retry decisions than baseline.")
    elif current.provider_retry > baseline.provider_retry:
        interpretation.append("Current stage required more final Provider-retry decisions than baseline.")
    else:
        interpretation.append("Final Provider-retry decisions were unchanged versus baseline.")
    if current.local_repair:
        interpretation.append(f"Current stage resolved {current.local_repair} chunk(s) through deterministic local repair.")
    if current.targeted_retry:
        interpretation.append(f"Current stage selected targeted retry for {current.targeted_retry} chunk(s).")
    if current.full_retry:
        interpretation.append(f"Current stage selected full retry for {current.full_retry} chunk(s).")
    if baseline.source_kind != current.source_kind:
        interpretation.append("Baseline and current metrics use different report generations; compare retry-tier fields cautiously.")
    return ProductionComparison(PRODUCTION_COMPARISON_VERSION, baseline, current, delta, interpretation)


def _render_markdown(comparison: ProductionComparison) -> str:
    b, c = comparison.baseline, comparison.current
    lines = [
        "# TE v6.0 Stage 10.2 Production Retry Comparison",
        "",
        f"Schema: `{comparison.version}`",
        "",
        "| Metric | Baseline | Current | Delta |",
        "|---|---:|---:|---:|",
    ]
    for key, label in (
        ("chunks_observed", "Chunks observed"),
        ("qa_attempts", "QA attempts"),
        ("provider_retry", "Provider retry decisions"),
        ("targeted_retry", "Targeted retry"),
        ("full_retry", "Full retry"),
        ("local_repair", "Local repair"),
        ("recovery_budget_used", "Recovery budget used"),
    ):
        lines.append(f"| {label} | {getattr(b, key)} | {getattr(c, key)} | {comparison.delta[key]:+d} |")
    lines.extend([
        f"| Retry rate | {b.retry_rate:.2%} | {c.retry_rate:.2%} | {comparison.delta['retry_rate']:+.2%} |",
        f"| Accepted rate | {b.accepted_rate:.2%} | {c.accepted_rate:.2%} | {comparison.delta['accepted_rate']:+.2%} |",
        "",
        "## Interpretation",
        "",
    ])
    lines.extend(f"- {item}" for item in comparison.interpretation)
    if b.warnings or c.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- Baseline: {item}" for item in b.warnings)
        lines.extend(f"- Current: {item}" for item in c.warnings)
    return "\n".join(lines) + "\n"


def write_comparison_reports(
    baseline_dir: str | Path,
    current_dir: str | Path,
    json_output: str | Path,
    markdown_output: str | Path | None = None,
) -> dict[str, Any]:
    comparison = compare_stage_outputs(baseline_dir, current_dir)
    payload = comparison.to_dict()
    json_path = Path(json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if markdown_output is not None:
        md_path = Path(markdown_output)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(_render_markdown(comparison), encoding="utf-8")
    return payload
