"""TIC Batch 6 human-guided correction records.

This module is offline and case-bound.  It creates reviewable drafts from the
two frozen Batch 5 failures, but never promotes Codex-authored wording to an
approved human correction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.shared.evidence import (
    canonical_json_bytes,
    read_json,
    resolve_project_relative_path,
    sha256_bytes,
    sha256_file,
    sha256_text,
)


BATCH5_CORPUS = "artifacts/tic_batch5/HUMAN_CONFIRMED_FAILURE_CORPUS_V2.json"
BATCH5_INDEX = "artifacts/tic_batch5/FAILURE_CASE_INDEX_V2.json"
BATCH5_STATISTICS = "artifacts/tic_batch5/FAILURE_CORPUS_V2_STATISTICS.json"
BATCH5_EXPANSION = "artifacts/tic_batch5/HISTORICAL_HUMAN_EVIDENCE_EXPANSION.json"
BATCH5_UNRESOLVED = "artifacts/tic_batch5/UNRESOLVED_HUMAN_EVIDENCE.json"
BATCH5_ARTIFACT_MANIFEST = (
    "artifacts/tic_batch5/HISTORICAL_HUMAN_EVIDENCE_EXPANSION_MANIFEST.json"
)
BATCH5_ROOT_MANIFEST = (
    "manifests/tic_batch5_historical_human_evidence_expansion_manifest.json"
)
FORMAL_INPUTS = (
    BATCH5_CORPUS,
    BATCH5_INDEX,
    BATCH5_STATISTICS,
    BATCH5_EXPANSION,
    BATCH5_UNRESOLVED,
)


def _object(root: Path, relative: str) -> dict[str, Any]:
    value = read_json(resolve_project_relative_path(root, relative, must_exist=True))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {relative}")
    return value


def with_integrity(value: dict[str, Any]) -> dict[str, Any]:
    body = {key: item for key, item in value.items() if key != "integrity"}
    return body | {
        "integrity": {
            "algorithm": "sha256",
            "payload_sha256": sha256_bytes(canonical_json_bytes(body)),
        }
    }


def validate_batch1_through_batch5_anchors(root: str | Path) -> dict[str, str]:
    """Validate frozen Batch 1-5 inputs without rebuilding any earlier batch."""
    base = Path(root).resolve()
    corpus = _object(base, BATCH5_CORPUS)
    anchors = dict(corpus["source_anchors"])
    for relative, expected in anchors.items():
        actual = sha256_file(resolve_project_relative_path(base, relative, must_exist=True))
        if actual != expected:
            raise ValueError(f"frozen Batch 1-4 anchor SHA mismatch: {relative}")

    release_manifest = _object(base, BATCH5_ROOT_MANIFEST)
    for relative in FORMAL_INPUTS:
        actual = sha256_file(resolve_project_relative_path(base, relative, must_exist=True))
        if release_manifest["files"].get(relative) != actual:
            raise ValueError(f"frozen Batch 5 input SHA mismatch: {relative}")
        anchors[relative] = actual

    for relative in (BATCH5_ARTIFACT_MANIFEST, BATCH5_ROOT_MANIFEST):
        anchors[relative] = sha256_file(
            resolve_project_relative_path(base, relative, must_exist=True)
        )
    return dict(sorted(anchors.items()))


def _minimal_case_patch(original: str, old: str, new: str) -> str:
    """Apply one explicit case-local span patch; never perform a global replace."""
    if original.count(old) != 1:
        raise ValueError("expected exactly one frozen correction span")
    start = original.index(old)
    return original[:start] + new + original[start + len(old) :]


def _draft_for_failure(failure: dict[str, Any]) -> tuple[str, str, bool]:
    original = failure["translation_text"]
    category = failure["failure_category"]
    if category == "subject_reference_shift":
        corrected = _minimal_case_patch(
            original,
            "鄭泰義也明白這種情況不可能是他故意製造的。",
            "他也會明白這種情況不可能是鄭泰義故意製造的。",
        )
        return corrected, "只修正認知主體及必要的施事指稱，不潤飾其他內容。", False
    if category == "lexical_choice":
        corrected = _minimal_case_patch(original, "人間", "人")
        return corrected, "只將固定案例中的錯誤詞彙「人間」修正為「人」。", True
    raise ValueError(f"unsupported Batch 6 failure category: {category}")


def build_correction_records(root: str | Path) -> dict[str, Any]:
    base = Path(root).resolve()
    validate_batch1_through_batch5_anchors(base)
    failures = _object(base, BATCH5_CORPUS)["failure_cases"]
    if [item["failure_category"] for item in failures] != [
        "subject_reference_shift",
        "lexical_choice",
    ]:
        raise ValueError("Batch 6 requires exactly the two frozen Batch 5 failures")

    records: list[dict[str, Any]] = []
    for failure in failures:
        draft, reason, terminology_changed = _draft_for_failure(failure)
        identity = {
            "failure_case_id": failure["failure_case_id"],
            "source_sha256": failure["source_sha256"],
            "original_translation_sha256": failure["translation_sha256"],
            "corrected_translation_sha256": sha256_text(draft),
        }
        body = {
            "schema_version": "tic.batch6.human-correction-record.v1",
            "correction_id": "TIC-CORR-B6-"
            + sha256_bytes(canonical_json_bytes(identity))[:20].upper(),
            "failure_case_id": failure["failure_case_id"],
            "case_id": failure["case_id"],
            "alignment_id": failure["alignment_id"],
            "evidence_id": failure["evidence_id"],
            "source_text": failure["source_text"],
            "original_translation": failure["translation_text"],
            "corrected_translation": draft,
            "corrected_translation_sha256": sha256_text(draft),
            "correction_status": "human_draft",
            "reviewer_type": "human_guided_codex_draft",
            "human_provenance": {
                "complete": True,
                "origin": "user_supplied_batch6_directive",
                "reviewer_id": "repository-owner",
                "semantic_constraint_supplied": True,
                "exact_wording_human_approved": False,
            },
            "review_reason": reason,
            "meaning_preserved": True,
            "unsupported_detail_added": False,
            "omission_introduced": False,
            "tone_changed": False,
            "terminology_changed": terminology_changed,
            "approved_at": None,
            "source_references": [BATCH5_CORPUS, BATCH5_EXPANSION],
        }
        records.append(with_integrity(body))

    return {
        "schema_version": "tic.batch6.human-correction-records.v1",
        "status": "human_review_pending",
        "items": records,
    }

