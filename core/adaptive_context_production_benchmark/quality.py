from __future__ import annotations

from typing import Any

from .model import ChunkEvidence


def _accepted(rows: tuple[ChunkEvidence, ...]) -> float:
    completed = tuple(row for row in rows if row.qa_status in {"accepted", "retry", "failed"})
    return round(sum(row.qa_status == "accepted" for row in completed) / len(completed), 6) if completed else 0.0


def compare_quality(paired: tuple[tuple[ChunkEvidence, ChunkEvidence], ...]) -> tuple[dict[str, Any], tuple[str, ...]]:
    b_rows = tuple(left for left, _ in paired); c_rows = tuple(right for _, right in paired)
    b_scores = tuple(row.quality_score for row in b_rows if row.quality_score is not None)
    c_scores = tuple(row.quality_score for row in c_rows if row.quality_score is not None)
    b_score = round(sum(b_scores) / len(b_scores), 6) if b_scores else 0.0
    c_score = round(sum(c_scores) / len(c_scores), 6) if c_scores else 0.0
    blockers: list[str] = []
    for baseline, candidate in paired:
        if candidate.ace_state != "activated":
            continue
        prefix = f"activated-chunk-{candidate.chunk_index}"
        if candidate.omission_issues > baseline.omission_issues: blockers.append(f"{prefix}-new-omission")
        if candidate.unsupported_detail_issues > baseline.unsupported_detail_issues: blockers.append(f"{prefix}-new-unsupported-detail")
        if candidate.completeness_issues > baseline.completeness_issues: blockers.append(f"{prefix}-completeness-regression")
        if baseline.qa_status == "accepted" and candidate.qa_status == "failed": blockers.append(f"{prefix}-accepted-to-failed")
        if baseline.quality_score is not None and (candidate.quality_score is None or candidate.quality_score < baseline.quality_score):
            blockers.append(f"{prefix}-quality-score-regression")
    metrics = {
        "baseline_quality_score": b_score, "candidate_quality_score": c_score, "quality_score_delta": round(c_score - b_score, 6),
        "baseline_accepted_rate": _accepted(b_rows), "candidate_accepted_rate": _accepted(c_rows),
        "baseline_omission_issues": sum(r.omission_issues for r in b_rows), "candidate_omission_issues": sum(r.omission_issues for r in c_rows),
        "baseline_unsupported_detail_issues": sum(r.unsupported_detail_issues for r in b_rows), "candidate_unsupported_detail_issues": sum(r.unsupported_detail_issues for r in c_rows),
        "baseline_completeness_issues": sum(r.completeness_issues for r in b_rows), "candidate_completeness_issues": sum(r.completeness_issues for r in c_rows),
        "baseline_recovery_count": sum(r.recovery_invocations for r in b_rows), "candidate_recovery_count": sum(r.recovery_invocations for r in c_rows),
        "baseline_naturalness_actions": sum(r.naturalness_actions for r in b_rows), "candidate_naturalness_actions": sum(r.naturalness_actions for r in c_rows),
        "baseline_naturalness_warnings": sum(r.naturalness_warnings for r in b_rows), "candidate_naturalness_warnings": sum(r.naturalness_warnings for r in c_rows),
        "quality_evidence_complete": bool(paired) and all(a.quality_evidence_complete and b.quality_evidence_complete for a, b in paired),
    }
    return metrics, tuple(dict.fromkeys(blockers))
