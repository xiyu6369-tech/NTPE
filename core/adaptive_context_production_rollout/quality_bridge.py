from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .metrics import RolloutMetrics
from .outcome import ProductionOutcome

_SUCCESS = {"success", "pass_with_warning"}
_OMISSION = ("OMISSION", "TOO_SHORT")
_UNSUPPORTED = ("UNSUPPORTED", "ADDED_DETAIL", "HALLUCINATION")


@dataclass(frozen=True)
class RollbackQualityInputs:
    new_issues: tuple[str, ...]
    quality_score: int | None
    baseline_quality_score: int | None
    qa_failure_rate: float | None
    baseline_qa_failure_rate: float | None
    anchor_mismatch: bool
    replacement_count: int


def _sha(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _read_object(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def snapshot_resume_chunks(stage_output: str | Path) -> frozenset[tuple[str, int]]:
    """Capture already-complete chunks before regression so resume hits cannot become ACE evidence."""
    found: set[tuple[str, int]] = set()
    for path in Path(stage_output).glob("*/original_ko_resume_state.json"):
        payload = _read_object(path) or {}
        chunks = payload.get("chunks")
        if not isinstance(chunks, Mapping):
            continue
        for key, row in chunks.items():
            if not isinstance(row, Mapping) or str(row.get("status", "")).lower() not in _SUCCESS:
                continue
            try:
                found.add((_sha(row.get("source_hash", "")), int(key)))
            except (TypeError, ValueError):
                continue
    return frozenset(found)


def prior_rollback_reasons(path: str | Path) -> tuple[str, ...]:
    payload = _read_object(Path(path)) or {}
    if payload.get("rollback") is not True or payload.get("mode") != "disabled":
        return ()
    reasons = payload.get("reasons")
    return tuple(str(reason) for reason in reasons or () if str(reason)) or ("prior-quality-rollback-active",)


def _issue_codes(value: object) -> tuple[str, ...]:
    codes: list[str] = []

    def visit(item: object, key: str = "") -> None:
        if isinstance(item, Mapping):
            if key in {"issues", "merged_issues"}:
                code = item.get("code") or item.get("issue_code")
                if code:
                    codes.append(str(code).strip().upper())
            for child_key, child in item.items():
                normalized = str(child_key).strip().lower()
                if normalized.endswith("issue_codes") and isinstance(child, (list, tuple)):
                    codes.extend(str(code).strip().upper() for code in child if str(code).strip())
                elif normalized in {"issues", "merged_issues"} and isinstance(child, (list, tuple)):
                    for row in child:
                        if isinstance(row, Mapping):
                            code = row.get("code") or row.get("issue_code")
                            if code:
                                codes.append(str(code).strip().upper())
                        elif isinstance(row, str) and row.strip():
                            codes.append(row.strip().upper())
                else:
                    visit(child, normalized)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child, key)

    visit(value)
    return tuple(dict.fromkeys(code for code in codes if code))


def _qa_values(row: Mapping[str, object]) -> tuple[str, int | None, tuple[str, ...], dict[str, object]]:
    qa = row.get("qa")
    if not isinstance(qa, Mapping):
        return "incomplete", None, (), {}
    unified = qa.get("unified_quality_report")
    quality = qa.get("quality_v5")
    status = str(qa.get("status") or qa.get("decision") or row.get("status") or "").strip().lower()
    raw_score = (
        unified.get("score") if isinstance(unified, Mapping) else None
    )
    if raw_score is None:
        raw_score = quality.get("quality_score") if isinstance(quality, Mapping) else qa.get("score")
    try:
        score = int(raw_score) if raw_score is not None else None
    except (TypeError, ValueError):
        score = None

    # Extract literary quality metrics from QA report metrics
    metrics = qa.get("metrics") if isinstance(qa.get("metrics"), Mapping) else unified.get("metrics") if isinstance(unified, Mapping) else {}
    lit_metrics = {}
    if isinstance(metrics, Mapping):
        lit_metrics = {
            "literary_quality_hits": metrics.get("literary_quality_hits", 0),
            "literary_quality_errors": metrics.get("literary_quality_errors", 0),
            "literary_quality_warnings": metrics.get("literary_quality_warnings", 0),
            "literary_quality_passed": metrics.get("literary_quality_passed", True),
            "literary_quality_issue_codes": metrics.get("literary_quality_issue_codes", []),
        }

    return status, score, _issue_codes(qa), lit_metrics


def _resume_for(output_dir: Path) -> dict[str, object] | None:
    matches = sorted(output_dir.glob("*_resume_state.json"))
    return _read_object(matches[0]) if matches else None


def collect_production_outcome(
    regression_result: Mapping[str, object],
    metrics: RolloutMetrics,
    *,
    root: str | Path,
    baseline_stage: str | None = None,
    resume_snapshot: frozenset[tuple[str, int]] = frozenset(),
    provider_status: str = "success",
) -> ProductionOutcome:
    activated = {
        (str(record.get("source_hash_sha256", "")), int(record.get("chunk_index", 0) or 0))
        for record in metrics.records if record.get("activated") is True
    }
    sampled_not_activated = sum(
        1 for record in metrics.records
        if record.get("decision") in {"sampled", "fallback", "shadow-compatible"} and record.get("activated") is not True
    )
    anchor_mismatch = sum(
        1 for record in metrics.records
        if any("anchor-mismatch" in str(reason) for reason in record.get("blockers", ()))
    )
    replacements = sum(1 for record in metrics.records if record.get("activated") is True and record.get("payload_changed") is True)
    current_scores: list[int] = []
    baseline_scores: list[int] = []
    new_issues: list[str] = []
    accepted = retry = failed = resume = incomplete = covered = 0
    reasons: list[str] = []
    lit_hits_total = 0
    lit_errors_total = 0
    lit_warnings_total = 0
    lit_passed_all = True
    lit_issue_codes: list[str] = []
    root_path = Path(root)

    for record in regression_result.get("records", ()) or ():
        if not isinstance(record, Mapping):
            continue
        set_name = str(record.get("name", ""))
        output_dir = Path(str(record.get("output_dir", "")))
        current = _resume_for(output_dir)
        chunks = current.get("chunks") if isinstance(current, Mapping) else None
        if not isinstance(chunks, Mapping):
            continue
        baseline_chunks: Mapping[str, object] = {}
        if baseline_stage:
            baseline = _resume_for(root_path / "tests" / "literary" / "outputs" / baseline_stage / set_name)
            if isinstance(baseline, Mapping) and isinstance(baseline.get("chunks"), Mapping):
                baseline_chunks = baseline["chunks"]  # type: ignore[assignment]
        for key, row in chunks.items():
            if not isinstance(row, Mapping):
                continue
            try:
                chunk = int(key)
            except (TypeError, ValueError):
                continue
            identity = (_sha(row.get("source_hash", "")), chunk)
            if identity not in activated:
                continue
            if identity in resume_snapshot:
                resume += 1
                continue
            status, score, issues, lit_metrics = _qa_values(row)
            if str(row.get("status", "")).lower() not in _SUCCESS | {"qa_failed"} or status == "incomplete" or score is None:
                incomplete += 1
                continue
            if str(row.get("status", "")).lower() == "qa_failed":
                failed += 1
            elif status in {"accepted", "pass", "pass_with_warning", "success"}:
                accepted += 1
            elif bool(row.get("qa", {}).get("retry_required")) if isinstance(row.get("qa"), Mapping) else False:
                retry += 1
            else:
                failed += 1
            current_scores.append(score)

            # Accumulate literary quality metrics
            lit_hits_total += int(lit_metrics.get("literary_quality_hits", 0))
            lit_errors_total += int(lit_metrics.get("literary_quality_errors", 0))
            lit_warnings_total += int(lit_metrics.get("literary_quality_warnings", 0))
            if not lit_metrics.get("literary_quality_passed", True):
                lit_passed_all = False
            lit_issue_codes.extend(lit_metrics.get("literary_quality_issue_codes", []))

            baseline_row = baseline_chunks.get(key)
            if not isinstance(baseline_row, Mapping) or baseline_row.get("source_hash") != row.get("source_hash"):
                reasons.append("baseline-evidence-missing")
                continue
            baseline_status, baseline_score, baseline_issues, baseline_lit_metrics = _qa_values(baseline_row)
            if baseline_score is None or baseline_status == "incomplete":
                reasons.append("baseline-evidence-incomplete")
                continue
            if baseline_status not in {"accepted", "pass", "pass_with_warning", "success"}:
                reasons.append("baseline-not-accepted")
                continue
            covered += 1
            baseline_scores.append(baseline_score)
            new_issues.extend(code for code in issues if code not in set(baseline_issues))

    effective_activated = max(0, len(activated) - resume)
    if not activated:
        reasons.append("no-activated-chunk")
    if incomplete:
        reasons.append("activated-qa-incomplete")
    if effective_activated and covered != effective_activated:
        reasons.append("baseline-coverage-incomplete")
    evidence_complete = effective_activated > 0 and incomplete == 0 and covered == effective_activated
    unique_issues = tuple(dict.fromkeys(new_issues))
    omission = tuple(code for code in unique_issues if any(marker in code for marker in _OMISSION))
    unsupported = tuple(code for code in unique_issues if any(marker in code for marker in _UNSUPPORTED))
    return ProductionOutcome(
        observed_chunks=len(metrics.records), activated_chunks=effective_activated,
        qa_accepted=accepted, qa_retry_required=retry, qa_failed=failed,
        quality_scores=tuple(current_scores), baseline_quality_scores=tuple(baseline_scores),
        new_issue_codes=unique_issues, omission_issues=omission, unsupported_detail_issues=unsupported,
        anchor_mismatch_count=anchor_mismatch, replacement_count=replacements,
        provider_timeout=int(provider_status == "timeout"), provider_503=int(provider_status == "503"),
        evidence_complete=evidence_complete, sampled_not_activated_chunks=sampled_not_activated,
        resume_chunks=resume, provider_incomplete_chunks=incomplete, baseline_covered_chunks=covered,
        evidence_reasons=tuple(dict.fromkeys(reasons)),
        literary_quality_hits=lit_hits_total,
        literary_quality_errors=lit_errors_total,
        literary_quality_warnings=lit_warnings_total,
        literary_quality_passed=lit_passed_all,
        literary_quality_issue_codes=tuple(dict.fromkeys(lit_issue_codes)),
    )


def rollback_quality_inputs(outcome: ProductionOutcome) -> RollbackQualityInputs:
    current = list(outcome.quality_scores)
    baseline = list(outcome.baseline_quality_scores)
    quality_score = baseline_score = None
    for candidate, reference in zip(current, baseline):
        if candidate < reference:
            quality_score, baseline_score = candidate, reference
            break
    if quality_score is None and current and len(current) == len(baseline):
        quality_score = round(sum(current) / len(current))
        baseline_score = round(sum(baseline) / len(baseline))
    # Baseline reports admitted by this bridge must be accepted; a non-accepted baseline is incomplete upstream.
    baseline_failure_rate = 0.0 if outcome.baseline_covered_chunks else None
    return RollbackQualityInputs(
        new_issues=outcome.new_issue_codes,
        quality_score=quality_score,
        baseline_quality_score=baseline_score,
        qa_failure_rate=outcome.qa_failure_rate,
        baseline_qa_failure_rate=baseline_failure_rate,
        anchor_mismatch=outcome.anchor_mismatch_count > 0,
        replacement_count=outcome.replacement_count,
    )
