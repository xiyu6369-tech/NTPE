"""TIC Batch 6.1 fixed-case active regression protection."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from core.shared.evidence import (
    canonical_json_bytes,
    read_json,
    sha256_bytes,
    sha256_file,
    sha256_text,
    write_canonical_json,
)

from .correction_records import with_integrity
from .human_approval import (
    APPROVALS_PATH,
    BATCH6_CORRECTIONS,
    BATCH6_REGRESSIONS,
    BATCH6_ROOT_CAUSES,
    BATCH61_DIR,
    CORRECTIONS_V2_PATH,
    build_human_approval_payloads,
    utc_approval_time,
    validate_batch1_through_batch6_anchors,
)


ACTIVE_REGRESSIONS_PATH = BATCH61_DIR / "ACTIVE_TRANSLATION_QUALITY_REGRESSIONS.json"
VALIDATION_PATH = BATCH61_DIR / "ACTIVE_REGRESSION_VALIDATION.json"
STATISTICS_PATH = BATCH61_DIR / "TIC_BATCH61_STATISTICS.json"
INDEX_PATH = BATCH61_DIR / "ACTIVE_REGRESSION_INDEX.json"
ROOT_MANIFEST = Path(
    "manifests/tic_batch61_human_approval_regression_activation_manifest.json"
)
RELEASE_DOCUMENT = Path(
    "docs/translation_intelligence/TIC_BATCH61_HUMAN_APPROVAL_AND_REGRESSION_ACTIVATION.md"
)
ROOT_TEST = Path("ntpe_tic_batch61_human_approval_regression_activation_test.py")
FOCUSED_TEST = Path(
    "tests/integration/tic_batch61_human_approval_regression_activation_test.py"
)
UNRELATED_TRANSLATION = "完全無關的固定測試句子。"


def _object(root: Path, relative: str | Path) -> dict[str, Any]:
    value = read_json(root / relative)
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {relative}")
    return value


def evaluate_active_regression(case: dict[str, Any], translation: str) -> dict[str, Any]:
    """Evaluate only the two frozen cases; unknown input fails closed."""
    if not isinstance(translation, str) or not translation.strip():
        return {"accepted": False, "checks": {"non_empty_text": False}}
    text = "".join(translation.split())
    category = case.get("category")
    if category == "subject_reference_shift":
        checks = {
            "frozen_context_present": "被拋在遠方的那個男人" in text and "理智清醒的人" in text,
            "far_man_is_cognitive_actor": "他也會明白這種情況" in text,
            "jeong_is_not_cognitive_actor": "鄭泰義也明白" not in text and "鄭泰義會明白" not in text,
            "jeong_remains_negative_intent_actor": "不可能是鄭泰義故意製造的" in text,
        }
    elif category == "lexical_choice":
        constraints = case.get("semantic_constraints", {})
        allowlist = tuple(constraints.get("human_person_allowlist", ()))
        checks = {
            "frozen_context_present": text.startswith("相當理性"),
            "forbidden_phrase_absent": "人間" not in text,
            "human_person_term_present": bool(allowlist) and any(text.endswith(term) for term in allowlist),
            "global_replacement_disabled": constraints.get("global_replacement_rule") is False,
        }
    else:
        return {"accepted": False, "checks": {"supported_fixed_case": False}}
    return {"accepted": all(checks.values()), "checks": checks}


def _active_case(
    draft: dict[str, Any], correction: dict[str, Any], approval: dict[str, Any]
) -> dict[str, Any]:
    if correction["correction_status"] != "human_approved":
        raise ValueError("draft corrections cannot activate regressions")
    if approval["approval_status"] != "human_approved":
        raise ValueError("human approval is required for activation")
    approved = approval["approved_translation"]
    digest = sha256_text(approved)
    if digest != approval["approved_translation_sha256"]:
        raise ValueError("approval translation SHA mismatch")
    if digest != correction["corrected_translation_sha256"]:
        raise ValueError("correction and approval translation SHA mismatch")
    body = {
        "schema_version": "tic.batch61.active-translation-quality-regression.v1",
        "regression_id": draft["regression_id"],
        "failure_case_id": draft["failure_case_id"],
        "approval_id": approval["approval_id"],
        "category": draft["category"],
        "source_text": draft["source_text"],
        "bad_translation": draft["bad_translation"],
        "approved_translation": approved,
        "must_preserve": draft["must_preserve"],
        "must_not_contain": draft["must_not_contain"],
        "semantic_constraints": draft["semantic_constraints"],
        "evaluation_type": draft["evaluation_type"],
        "blocking": True,
        "review_status": "human_approved",
        "regression_status": "active",
        "source_sha256": draft["source_sha256"],
        "bad_translation_sha256": draft["bad_translation_sha256"],
        "approved_translation_sha256": digest,
    }
    return with_integrity(body)


def _boundary() -> dict[str, Any]:
    return {
        "provider_executed": False,
        "network_requests": 0,
        "new_translation_generated": False,
        "historical_translation_modified": False,
        "runtime_modified": False,
        "provider_modified": False,
        "prompt_modified": False,
        "qa_engine_modified": False,
        "stage11_modified": False,
        "stage12_modified": False,
        "batch6_artifacts_modified": False,
        "root_cause_status_modified": False,
        "human_approvals_created": 2,
        "human_approved_corrections": 2,
        "active_regressions": 2,
        "pending_regressions": 0,
        "production_fix_applied": False,
        "translation_quality_improved": False,
        "fixed_case_regression_protection_created": True,
        "tic_batch7_started": False,
    }


def build_batch61_payloads(
    root: str | Path, approved_at: str
) -> dict[str, dict[str, Any]]:
    base = Path(root).resolve()
    approval_payloads = build_human_approval_payloads(base, approved_at)
    approvals_payload = approval_payloads[APPROVALS_PATH.as_posix()]
    corrections_payload = approval_payloads[CORRECTIONS_V2_PATH.as_posix()]
    draft_regressions = _object(base, BATCH6_REGRESSIONS)["items"]
    draft_corrections = _object(base, BATCH6_CORRECTIONS)["items"]
    roots = _object(base, BATCH6_ROOT_CAUSES)["items"]
    approval_map = {item["failure_case_id"]: item for item in approvals_payload["items"]}
    correction_map = {item["failure_case_id"]: item for item in corrections_payload["items"]}
    if {item["failure_case_id"] for item in draft_regressions} != set(approval_map):
        raise ValueError("failure and regression traceability mismatch")
    if {item["failure_case_id"] for item in draft_corrections} != set(approval_map):
        raise ValueError("failure and correction traceability mismatch")
    if any(item["root_cause_status"] != "evidence_supported" for item in roots):
        raise ValueError("root cause status must remain evidence_supported")

    active = [
        _active_case(item, correction_map[item["failure_case_id"]], approval_map[item["failure_case_id"]])
        for item in draft_regressions
    ]
    validation_items = []
    for case in active:
        bad = evaluate_active_regression(case, case["bad_translation"])
        approved = evaluate_active_regression(case, case["approved_translation"])
        unrelated = evaluate_active_regression(case, UNRELATED_TRANSLATION)
        repeated = evaluate_active_regression(case, case["approved_translation"])
        if bad["accepted"] or not approved["accepted"] or unrelated["accepted"]:
            raise ValueError(f"regression activation checks failed: {case['regression_id']}")
        validation_items.append(
            with_integrity(
                {
                    "regression_id": case["regression_id"],
                    "failure_case_id": case["failure_case_id"],
                    "category": case["category"],
                    "bad_translation_fails": True,
                    "bad_translation_result": bad,
                    "approved_translation_passes": True,
                    "approved_translation_result": approved,
                    "unrelated_translation_rejected": True,
                    "unrelated_translation_result": unrelated,
                    "deterministic": approved == repeated,
                }
            )
        )
    counts = Counter(item["category"] for item in active)
    boundary = _boundary()
    anchors = validate_batch1_through_batch6_anchors(base)
    active_payload = {
        "schema_version": "tic.batch61.active-translation-quality-regressions.v1",
        "review_status": "human_approved",
        "regression_status": "active",
        "items": active,
    }
    validation_payload = {
        "schema_version": "tic.batch61.active-regression-validation.v1",
        "total_active_regressions": len(active),
        "bad_translation_fail_count": sum(item["bad_translation_fails"] for item in validation_items),
        "approved_translation_pass_count": sum(item["approved_translation_passes"] for item in validation_items),
        "unrelated_translation_rejected_count": sum(item["unrelated_translation_rejected"] for item in validation_items),
        "subject_shift_active": counts["subject_reference_shift"] == 1,
        "lexical_choice_active": counts["lexical_choice"] == 1,
        "deterministic": all(item["deterministic"] for item in validation_items),
        "provider_executed": False,
        "production_modified": False,
        "validation_results": validation_items,
        "source_anchors": anchors,
        "boundary": boundary,
    }
    statistics_payload = {
        "schema_version": "tic.batch61.statistics.v1",
        "approvals_created": len(approvals_payload["items"]),
        "human_approved_corrections": len(corrections_payload["items"]),
        "active_regressions": len(active),
        "pending_regressions": 0,
        "failure_categories": dict(sorted(counts.items())),
        "bad_translation_fail_count": validation_payload["bad_translation_fail_count"],
        "approved_translation_pass_count": validation_payload["approved_translation_pass_count"],
        "unrelated_translation_rejected_count": validation_payload["unrelated_translation_rejected_count"],
        "production_fixes_applied": 0,
        "root_causes_modified": 0,
    }
    index_payload = {
        "schema_version": "tic.batch61.active-regression-index.v1",
        "items": [
            {
                "regression_id": case["regression_id"],
                "failure_case_id": case["failure_case_id"],
                "approval_id": case["approval_id"],
                "correction_id": correction_map[case["failure_case_id"]]["correction_id"],
                "failure_category": case["category"],
                "evaluation_type": case["evaluation_type"],
                "regression_status": case["regression_status"],
                "review_status": case["review_status"],
                "blocking": case["blocking"],
            }
            for case in active
        ],
    }
    return approval_payloads | {
        ACTIVE_REGRESSIONS_PATH.as_posix(): active_payload,
        VALIDATION_PATH.as_posix(): validation_payload,
        STATISTICS_PATH.as_posix(): statistics_payload,
        INDEX_PATH.as_posix(): index_payload,
    }


def _artifact_approval_time(root: Path) -> str:
    existing = root / APPROVALS_PATH
    if existing.is_file():
        value = _object(root, APPROVALS_PATH).get("approved_at")
        if isinstance(value, str) and value.endswith("Z"):
            return value
        raise ValueError("existing approval artifact has invalid approved_at")
    return utc_approval_time()


def generate_batch61_artifacts(
    root: str | Path, approved_at: str | None = None
) -> dict[str, Path]:
    base = Path(root).resolve()
    timestamp = approved_at or _artifact_approval_time(base)
    payloads = build_batch61_payloads(base, timestamp)
    for relative, payload in payloads.items():
        write_canonical_json(base / relative, payload)
    return {relative: base / relative for relative in payloads}


def generate_batch61_manifest(root: str | Path) -> Path:
    base = Path(root).resolve()
    validation = _object(base, VALIDATION_PATH)
    files = [
        "core/translation_intelligence_corpus/human_approval.py",
        "core/translation_intelligence_corpus/regression_activation.py",
        APPROVALS_PATH.as_posix(),
        CORRECTIONS_V2_PATH.as_posix(),
        ACTIVE_REGRESSIONS_PATH.as_posix(),
        VALIDATION_PATH.as_posix(),
        STATISTICS_PATH.as_posix(),
        INDEX_PATH.as_posix(),
        RELEASE_DOCUMENT.as_posix(),
        ROOT_TEST.as_posix(),
        FOCUSED_TEST.as_posix(),
    ]
    manifest = {
        "schema_version": "tic.batch61.release-manifest.v1",
        "batch": "TIC Batch 6.1 - Human Approval and Regression Activation",
        "status": "TIC Batch 6.1 Completed",
        "next_batch_status": "TIC Batch 7 Not Started",
        "source_anchors": validation["source_anchors"],
        "files": {relative: sha256_file(base / relative) for relative in files},
        "tests": {
            "root": ROOT_TEST.as_posix(),
            "focused_integration": FOCUSED_TEST.as_posix(),
        },
        "boundary": validation["boundary"],
        "sha256": {"algorithm": "sha256", "self_hash_excluded": True},
    }
    write_canonical_json(base / ROOT_MANIFEST, manifest)
    return base / ROOT_MANIFEST


def main() -> int:
    parser = argparse.ArgumentParser(description="Build TIC Batch 6.1 offline artifacts")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    generate_batch61_artifacts(args.root)
    if args.manifest:
        generate_batch61_manifest(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
