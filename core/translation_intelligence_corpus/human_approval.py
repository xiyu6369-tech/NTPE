"""TIC Batch 6.1 explicit human approval records.

This module promotes only the two frozen Batch 6 correction drafts whose exact
wording was approved in the Batch 6.1 user directive.  It is offline,
case-bound, and does not modify any earlier artifact.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.shared.evidence import (
    canonical_json_bytes,
    read_json,
    resolve_project_relative_path,
    sha256_bytes,
    sha256_file,
    sha256_text,
    write_canonical_json,
)

from .correction_records import with_integrity


BATCH6_DIR = Path("artifacts/tic_batch6")
BATCH61_DIR = Path("artifacts/tic_batch61")
BATCH6_CORRECTIONS = BATCH6_DIR / "HUMAN_CORRECTION_RECORDS.json"
BATCH6_ROOT_CAUSES = BATCH6_DIR / "ROOT_CAUSE_RECORDS.json"
BATCH6_REGRESSIONS = BATCH6_DIR / "TRANSLATION_QUALITY_REGRESSION_CASES.json"
BATCH6_VALIDATION = BATCH6_DIR / "QUALITY_REGRESSION_VALIDATION.json"
BATCH6_STATISTICS = BATCH6_DIR / "TIC_BATCH6_STATISTICS.json"
BATCH6_INDEX = BATCH6_DIR / "QUALITY_REGRESSION_INDEX.json"
BATCH6_MANIFEST = Path(
    "manifests/tic_batch6_human_correction_root_cause_regression_manifest.json"
)
APPROVALS_PATH = BATCH61_DIR / "HUMAN_APPROVAL_RECORDS.json"
CORRECTIONS_V2_PATH = BATCH61_DIR / "HUMAN_CORRECTION_RECORDS_V2.json"
FORMAL_BATCH6_INPUTS = (
    BATCH6_CORRECTIONS,
    BATCH6_ROOT_CAUSES,
    BATCH6_REGRESSIONS,
    BATCH6_VALIDATION,
    BATCH6_STATISTICS,
    BATCH6_INDEX,
)
APPROVED_TRANSLATIONS = {
    "subject_reference_shift": "被拋在遠方的那個男人雖然像個怪物，但至少他仍然是個理智清醒的人，他也會明白這種情況不可能是鄭泰義故意製造的。",
    "lexical_choice": "相當理性的人",
}


def _object(root: Path, relative: str | Path) -> dict[str, Any]:
    value = read_json(
        resolve_project_relative_path(root, Path(relative).as_posix(), must_exist=True)
    )
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {relative}")
    return value


def utc_approval_time() -> str:
    """Return the execution time in a stable UTC representation."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def validate_batch1_through_batch6_anchors(root: str | Path) -> dict[str, str]:
    """Fail closed unless the frozen Batch 1-6 inputs match the Batch 6 release."""
    base = Path(root).resolve()
    manifest = _object(base, BATCH6_MANIFEST)
    anchors = dict(manifest["source_anchors"])
    for relative, expected in anchors.items():
        if sha256_file(base / relative) != expected:
            raise ValueError(f"frozen Batch 1-5 anchor SHA mismatch: {relative}")
    for relative in FORMAL_BATCH6_INPUTS:
        key = relative.as_posix()
        actual = sha256_file(base / relative)
        if manifest["files"].get(key) != actual:
            raise ValueError(f"frozen Batch 6 input SHA mismatch: {key}")
        anchors[key] = actual
    anchors[BATCH6_MANIFEST.as_posix()] = sha256_file(base / BATCH6_MANIFEST)
    return dict(sorted(anchors.items()))


def _approval_id(correction: dict[str, Any], regression: dict[str, Any]) -> str:
    identity = {
        "correction_id": correction["correction_id"],
        "failure_case_id": correction["failure_case_id"],
        "regression_id": regression["regression_id"],
        "approved_translation_sha256": correction["corrected_translation_sha256"],
    }
    return "TIC-APPROVAL-B61-" + sha256_bytes(canonical_json_bytes(identity))[:20].upper()


def build_human_approval_payloads(
    root: str | Path, approved_at: str
) -> dict[str, dict[str, Any]]:
    """Build the two approvals and correction V2 records without writing files."""
    if not isinstance(approved_at, str) or not approved_at.endswith("Z"):
        raise ValueError("approved_at must be an explicit UTC timestamp ending in Z")
    base = Path(root).resolve()
    anchors = validate_batch1_through_batch6_anchors(base)
    corrections = _object(base, BATCH6_CORRECTIONS)["items"]
    regressions = _object(base, BATCH6_REGRESSIONS)["items"]
    roots = _object(base, BATCH6_ROOT_CAUSES)["items"]
    regression_map = {item["failure_case_id"]: item for item in regressions}
    root_map = {item["failure_case_id"]: item for item in roots}
    if len(corrections) != 2 or len(regression_map) != 2 or len(root_map) != 2:
        raise ValueError("Batch 6.1 requires exactly two traceable Batch 6 cases")

    approvals: list[dict[str, Any]] = []
    correction_v2: list[dict[str, Any]] = []
    for correction in corrections:
        failure_id = correction["failure_case_id"]
        regression = regression_map.get(failure_id)
        root = root_map.get(failure_id)
        if regression is None or root is None:
            raise ValueError(f"untraceable Batch 6 case: {failure_id}")
        category = regression["category"]
        approved = APPROVED_TRANSLATIONS.get(category)
        if approved is None or correction["corrected_translation"] != approved:
            raise ValueError(f"approved wording does not match frozen draft: {failure_id}")
        if root["root_cause_status"] != "evidence_supported":
            raise ValueError("Batch 6.1 must not promote a root cause conclusion")
        approval_id = _approval_id(correction, regression)
        approval_source = "user_directive:TIC Batch 6.1"
        approval = with_integrity(
            {
                "schema_version": "tic.batch61.human-approval-record.v1",
                "approval_id": approval_id,
                "correction_id": correction["correction_id"],
                "failure_case_id": failure_id,
                "regression_id": regression["regression_id"],
                "approved_translation": approved,
                "approved_translation_sha256": sha256_text(approved),
                "approval_status": "human_approved",
                "reviewer_type": "human",
                "human_provenance": "explicit_user_approval",
                "approval_source": approval_source,
                "approval_reason": "使用者明確批准 Batch 6 correction draft 的精確文字。",
                "approved_at": approved_at,
                "meaning_preserved": correction["meaning_preserved"],
                "unsupported_detail_added": correction["unsupported_detail_added"],
                "omission_introduced": correction["omission_introduced"],
                "tone_changed": correction["tone_changed"],
                "terminology_changed": correction["terminology_changed"],
                "source_references": [
                    BATCH6_CORRECTIONS.as_posix(),
                    BATCH6_REGRESSIONS.as_posix(),
                    BATCH6_ROOT_CAUSES.as_posix(),
                ],
            }
        )
        provenance = dict(correction["human_provenance"])
        provenance.update(
            {
                "exact_wording_human_approved": True,
                "approval_origin": "explicit_user_approval",
            }
        )
        v2_body = {key: value for key, value in correction.items() if key != "integrity"}
        v2_body.update(
            {
                "schema_version": "tic.batch61.human-correction-record-v2.v1",
                "correction_status": "human_approved",
                "reviewer_type": "human",
                "human_provenance": provenance,
                "exact_wording_human_approved": True,
                "approved_at": approved_at,
                "approval_id": approval_id,
                "approval_source": approval_source,
            }
        )
        approvals.append(approval)
        correction_v2.append(with_integrity(v2_body))

    approval_payload = {
        "schema_version": "tic.batch61.human-approval-records.v1",
        "status": "human_approved",
        "approved_at": approved_at,
        "source_anchors": anchors,
        "items": approvals,
    }
    correction_payload = {
        "schema_version": "tic.batch61.human-correction-records-v2.v1",
        "status": "human_approved",
        "approved_at": approved_at,
        "items": correction_v2,
    }
    return {
        APPROVALS_PATH.as_posix(): approval_payload,
        CORRECTIONS_V2_PATH.as_posix(): correction_payload,
    }


def write_human_approval_artifacts(
    root: str | Path, approved_at: str
) -> dict[str, Path]:
    base = Path(root).resolve()
    payloads = build_human_approval_payloads(base, approved_at)
    for relative, payload in payloads.items():
        write_canonical_json(base / relative, payload)
    return {relative: base / relative for relative in payloads}
