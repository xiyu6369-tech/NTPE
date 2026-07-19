from __future__ import annotations

from typing import Mapping, Sequence

from .models import CanaryPairRecord


CHECKLIST = (
    "completeness",
    "hallucination",
    "character_consistency",
    "honorific_consistency",
    "dialogue_continuity",
    "speaker_continuity",
    "context_continuity",
    "pronoun_resolution",
    "naturalness",
    "era_wording",
    "hangul_remaining",
)
COMPARISON_VALUES = ("Improved", "Same", "Regressed")
PASS_REQUIRED_NON_REGRESSION = {
    "completeness", "hallucination", "character_consistency",
    "context_continuity", "dialogue_continuity", "naturalness",
}


def build_comparison_report(
    pairs: Sequence[CanaryPairRecord],
    reviews: Mapping[str, Mapping[str, str]] | None = None,
    *,
    corpus_human_reviewed: bool,
) -> dict[str, object]:
    supplied = reviews or {}
    rows: list[dict[str, object]] = []
    counts = {value: 0 for value in COMPARISON_VALUES}
    reviewed_rows = 0
    for pair in pairs:
        case_review = supplied.get(pair.case_id, {})
        checklist_rows = []
        for dimension in CHECKLIST:
            result = case_review.get(dimension, "Same")
            if result not in COMPARISON_VALUES:
                raise ValueError(f"invalid comparison value:{dimension}:{result}")
            evidence_status = "human_reviewed" if dimension in case_review else "insufficient_evidence"
            reviewed_rows += int(evidence_status == "human_reviewed")
            counts[result] += 1
            checklist_rows.append({
                "dimension": dimension,
                "result": result,
                "evidence_status": evidence_status,
            })
        rows.append({
            "case_id": pair.case_id,
            "translation_pair_complete": bool(
                pair.baseline.translation_executed and pair.candidate.translation_executed
            ),
            "checklist": checklist_rows,
        })

    expected_rows = len(pairs) * len(CHECKLIST)
    all_reviewed = expected_rows > 0 and reviewed_rows == expected_rows
    no_required_regression = all(
        row["result"] != "Regressed"
        for case in rows
        for row in case["checklist"]
        if row["dimension"] in PASS_REQUIRED_NON_REGRESSION
    )
    pairs_complete = bool(pairs) and all(
        pair.parity_verified
        and pair.only_feature_flags_differ
        and pair.baseline.translation_executed
        and pair.candidate.translation_executed
        for pair in pairs
    )
    canary_pass = corpus_human_reviewed and all_reviewed and pairs_complete and no_required_regression
    return {
        "status": "PASS" if canary_pass else "FAIL_CLOSED_INSUFFICIENT_QUALITY_EVIDENCE",
        "canary_pass": canary_pass,
        "corpus_human_reviewed": corpus_human_reviewed,
        "translation_pairs_complete": pairs_complete,
        "reviewed_checklist_rows": reviewed_rows,
        "expected_checklist_rows": expected_rows,
        "allowed_results": list(COMPARISON_VALUES),
        "statistics": counts,
        "chunks": rows,
    }
