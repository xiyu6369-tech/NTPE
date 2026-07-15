"""Deterministic, fixed-case TIC Batch 6 quality regressions."""

from __future__ import annotations

import argparse
from collections import Counter
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

from .correction_records import (
    BATCH5_CORPUS,
    BATCH5_EXPANSION,
    BATCH5_INDEX,
    BATCH5_STATISTICS,
    BATCH5_UNRESOLVED,
    build_correction_records,
    validate_batch1_through_batch5_anchors,
    with_integrity,
)
from .root_cause_records import build_root_cause_records


ARTIFACT_DIR = Path("artifacts/tic_batch6")
CORRECTIONS_PATH = ARTIFACT_DIR / "HUMAN_CORRECTION_RECORDS.json"
ROOT_CAUSES_PATH = ARTIFACT_DIR / "ROOT_CAUSE_RECORDS.json"
REGRESSION_CASES_PATH = ARTIFACT_DIR / "TRANSLATION_QUALITY_REGRESSION_CASES.json"
VALIDATION_PATH = ARTIFACT_DIR / "QUALITY_REGRESSION_VALIDATION.json"
STATISTICS_PATH = ARTIFACT_DIR / "TIC_BATCH6_STATISTICS.json"
INDEX_PATH = ARTIFACT_DIR / "QUALITY_REGRESSION_INDEX.json"
ROOT_MANIFEST = Path(
    "manifests/tic_batch6_human_correction_root_cause_regression_manifest.json"
)
SUPPORTED_EVALUATION_TYPES = (
    "exact_constraint",
    "forbidden_phrase",
    "required_semantic_actor",
    "lexical_choice",
)


def _object(root: Path, relative: str) -> dict[str, Any]:
    value = read_json(resolve_project_relative_path(root, relative, must_exist=True))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {relative}")
    return value


def _compact(text: str) -> str:
    return "".join(text.split())


def evaluate_regression_case(case: dict[str, Any], translation: str) -> dict[str, Any]:
    """Evaluate one frozen case. Unknown categories and non-text fail closed."""
    if not isinstance(translation, str) or not translation.strip():
        return {"accepted": False, "checks": {"non_empty_text": False}}
    text = _compact(translation)
    category = case.get("category")

    if category == "subject_reference_shift":
        cognitive_patterns = ("他也會明白", "他會明白", "那個男人也會明白", "那個男人會明白")
        forbidden_patterns = ("鄭泰義也明白", "鄭泰義會明白", "鄭泰義也理解", "鄭泰義會理解")
        checks = {
            "far_man_context_present": "遠方" in text and "男人" in text,
            "far_man_is_cognitive_actor": any(item in text for item in cognitive_patterns),
            "jeong_is_not_cognitive_actor": not any(item in text for item in forbidden_patterns),
            "jeong_remains_intent_actor": "鄭泰義故意製造" in text,
            "situation_semantics_present": "這種情況不可能" in text,
        }
    elif category == "lexical_choice":
        allowlist = tuple(case["semantic_constraints"]["human_person_allowlist"])
        checks = {
            "fixed_context_present": "相當理性" in text,
            "forbidden_phrase_absent": "人間" not in text,
            "human_person_term_present": any(text.endswith(item) for item in allowlist),
        }
    else:
        return {"accepted": False, "checks": {"supported_fixed_case": False}}
    return {"accepted": all(checks.values()), "checks": checks}


def _regression_id(failure: dict[str, Any]) -> str:
    identity = {
        "failure_case_id": failure["failure_case_id"],
        "category": failure["failure_category"],
        "source_sha256": failure["source_sha256"],
        "bad_translation_sha256": failure["translation_sha256"],
    }
    return "TIC-REG-B6-" + sha256_bytes(canonical_json_bytes(identity))[:20].upper()


def _regression_case(
    failure: dict[str, Any], correction: dict[str, Any]
) -> dict[str, Any]:
    category = failure["failure_category"]
    approved = (
        correction["corrected_translation"]
        if correction["correction_status"] == "human_approved"
        else None
    )
    if category == "subject_reference_shift":
        evaluation_type = "required_semantic_actor"
        evaluation_components = ["exact_constraint", "required_semantic_actor"]
        must_preserve = ["前述遠方的男人是理解此情況的主體", "鄭泰義是故意製造行為的否定施事"]
        must_not_contain = ["鄭泰義也明白", "鄭泰義會明白"]
        constraints = {
            "required_semantic_actor": "前述遠方的男人",
            "forbidden_semantic_actor": "鄭泰義",
            "scope": "TIC-FAIL-B4-FAA4C8AD021D6103DDA6 only",
        }
    elif category == "lexical_choice":
        evaluation_type = "lexical_choice"
        evaluation_components = ["forbidden_phrase", "lexical_choice"]
        must_preserve = ["相當理性", "human_person meaning"]
        must_not_contain = ["人間"]
        constraints = {
            "forbidden_phrase": "人間",
            "required_meaning_category": "human_person",
            "human_person_allowlist": ["人", "人物", "人類"],
            "scope": "TIC-FAIL-B5-B9C4571532433778FB01 only",
            "global_replacement_rule": False,
        }
    else:
        raise ValueError(f"unsupported Batch 6 failure category: {category}")

    return with_integrity(
        {
            "schema_version": "tic.batch6.translation-quality-regression-case.v1",
            "regression_id": _regression_id(failure),
            "failure_case_id": failure["failure_case_id"],
            "category": category,
            "source_text": failure["source_text"],
            "bad_translation": failure["translation_text"],
            "approved_translation": approved,
            "draft_translation": correction["corrected_translation"],
            "must_preserve": must_preserve,
            "must_not_contain": must_not_contain,
            "semantic_constraints": constraints,
            "evaluation_type": evaluation_type,
            "evaluation_components": evaluation_components,
            "blocking": failure["blocking"],
            "review_status": "pending_human_approval",
            "regression_status": "pending_human_correction",
            "source_sha256": failure["source_sha256"],
            "bad_translation_sha256": failure["translation_sha256"],
            "approved_translation_sha256": (
                sha256_text(approved) if approved is not None else None
            ),
            "draft_translation_sha256": correction["corrected_translation_sha256"],
        }
    )


def _validation(cases: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    unrelated = "這是一段與固定案例無關、也未經人工批准的譯文。"
    for case in cases:
        bad = evaluate_regression_case(case, case["bad_translation"])
        draft = evaluate_regression_case(case, case["draft_translation"])
        unrelated_result = evaluate_regression_case(case, unrelated)
        repeat = evaluate_regression_case(case, case["draft_translation"])
        approved_result = (
            evaluate_regression_case(case, case["approved_translation"])
            if case["approved_translation"] is not None
            else None
        )
        items.append(
            with_integrity(
                {
                    "regression_id": case["regression_id"],
                    "failure_case_id": case["failure_case_id"],
                    "category": case["category"],
                    "regression_status": case["regression_status"],
                    "bad_translation_fails": bad["accepted"] is False,
                    "bad_translation_result": bad,
                    "approved_translation_passes": (
                        approved_result["accepted"] if approved_result else None
                    ),
                    "approved_translation_result": approved_result,
                    "draft_translation_satisfies_constraints": draft["accepted"],
                    "draft_translation_result": draft,
                    "unrelated_translation_not_accepted": (
                        unrelated_result["accepted"] is False
                    ),
                    "deterministic": draft == repeat,
                }
            )
        )
    return {
        "schema_version": "tic.batch6.quality-regression-validation.v1",
        "items": items,
        "all_bad_translations_fail": all(item["bad_translation_fails"] for item in items),
        "all_unrelated_translations_rejected": all(
            item["unrelated_translation_not_accepted"] for item in items
        ),
        "deterministic": all(item["deterministic"] for item in items),
    }


def _statistics(
    corrections: list[dict[str, Any]],
    roots: list[dict[str, Any]],
    regressions: list[dict[str, Any]],
    validation: list[dict[str, Any]],
) -> dict[str, Any]:
    correction_counts = Counter(item["correction_status"] for item in corrections)
    root_counts = Counter(item["root_cause_status"] for item in roots)
    regression_counts = Counter(item["regression_status"] for item in regressions)
    return {
        "schema_version": "tic.batch6.statistics.v1",
        "failure_cases_processed": len(corrections),
        "human_approved_corrections": correction_counts["human_approved"],
        "human_draft_corrections": correction_counts["human_draft"],
        "corrections_unavailable": correction_counts["not_available"],
        "root_causes_human_confirmed": root_counts["human_confirmed"],
        "root_causes_evidence_supported": root_counts["evidence_supported"],
        "root_causes_insufficient_evidence": root_counts["insufficient_evidence"],
        "regression_cases_created": len(regressions),
        "regression_cases_active": regression_counts["active"],
        "regression_cases_pending": regression_counts["pending_human_correction"],
        "bad_translation_fail_count": sum(
            item["bad_translation_fails"] for item in validation
        ),
        "approved_translation_pass_count": sum(
            item["approved_translation_passes"] is True for item in validation
        ),
        "draft_translation_constraint_pass_count": sum(
            item["draft_translation_satisfies_constraints"] for item in validation
        ),
        "categories": sorted(item["category"] for item in regressions),
        "recommended_fix_locations": sorted(
            {item["recommended_fix_location"] for item in roots}
        ),
    }


def _index(
    corrections: list[dict[str, Any]],
    roots: list[dict[str, Any]],
    regressions: list[dict[str, Any]],
) -> dict[str, Any]:
    correction_map = {item["failure_case_id"]: item for item in corrections}
    root_map = {item["failure_case_id"]: item for item in roots}
    items = []
    for regression in regressions:
        failure_id = regression["failure_case_id"]
        correction = correction_map[failure_id]
        root = root_map[failure_id]
        items.append(
            {
                "regression_id": regression["regression_id"],
                "failure_case_id": failure_id,
                "failure_category": regression["category"],
                "root_cause_status": root["root_cause_status"],
                "affected_layer": root["affected_layer"],
                "recommended_fix_location": root["recommended_fix_location"],
                "correction_status": correction["correction_status"],
                "regression_status": regression["regression_status"],
                "blocking": regression["blocking"],
            }
        )
    return {"schema_version": "tic.batch6.quality-regression-index.v1", "items": items}


def build_batch6_payloads(root: str | Path) -> dict[str, dict[str, Any]]:
    base = Path(root).resolve()
    anchors = validate_batch1_through_batch5_anchors(base)
    failures = _object(base, BATCH5_CORPUS)["failure_cases"]
    corrections = build_correction_records(base)
    roots = build_root_cause_records(failures)
    correction_map = {
        item["failure_case_id"]: item for item in corrections["items"]
    }
    regressions = {
        "schema_version": "tic.batch6.translation-quality-regression-cases.v1",
        "supported_evaluation_types": list(SUPPORTED_EVALUATION_TYPES),
        "items": [
            _regression_case(item, correction_map[item["failure_case_id"]])
            for item in failures
        ],
    }
    validation = _validation(regressions["items"])
    statistics = _statistics(
        corrections["items"], roots["items"], regressions["items"], validation["items"]
    )
    index = _index(corrections["items"], roots["items"], regressions["items"])
    boundary = {
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
        "failure_corpus_v2_modified": False,
        "human_correction_records_created": True,
        "root_cause_records_created": True,
        "quality_regression_cases_created": True,
        "production_fix_applied": False,
        "translation_quality_improved": False,
        "translation_quality_regression_guard_created": True,
        "tic_batch7_started": False,
    }
    validation["source_anchors"] = anchors
    validation["boundary"] = boundary
    return {
        CORRECTIONS_PATH.as_posix(): corrections,
        ROOT_CAUSES_PATH.as_posix(): roots,
        REGRESSION_CASES_PATH.as_posix(): regressions,
        VALIDATION_PATH.as_posix(): validation,
        STATISTICS_PATH.as_posix(): statistics,
        INDEX_PATH.as_posix(): index,
    }


def generate_batch6_artifacts(root: str | Path) -> dict[str, Path]:
    base = Path(root).resolve()
    payloads = build_batch6_payloads(base)
    for relative, payload in payloads.items():
        write_canonical_json(base / relative, payload)
    return {relative: base / relative for relative in payloads}


def generate_batch6_manifest(root: str | Path) -> Path:
    base = Path(root).resolve()
    validation = _object(base, VALIDATION_PATH.as_posix())
    files = [
        "core/translation_intelligence_corpus/correction_records.py",
        "core/translation_intelligence_corpus/root_cause_records.py",
        "core/translation_intelligence_corpus/quality_regression.py",
        CORRECTIONS_PATH.as_posix(),
        ROOT_CAUSES_PATH.as_posix(),
        REGRESSION_CASES_PATH.as_posix(),
        VALIDATION_PATH.as_posix(),
        STATISTICS_PATH.as_posix(),
        INDEX_PATH.as_posix(),
        "docs/translation_intelligence/TIC_BATCH6_HUMAN_CORRECTION_ROOT_CAUSE_REGRESSION.md",
        "ntpe_tic_batch6_human_correction_root_cause_regression_test.py",
        "tests/integration/tic_batch6_human_correction_root_cause_regression_test.py",
    ]
    manifest = {
        "schema_version": "tic.batch6.release-manifest.v1",
        "batch": "TIC Batch 6 - Human Correction, Root Cause, and Quality Regression",
        "status": "TIC Batch 6 Completed",
        "next_batch_status": "TIC Batch 7 Not Started",
        "source_anchors": validation["source_anchors"],
        "files": {relative: sha256_file(base / relative) for relative in files},
        "tests": {
            "root": "ntpe_tic_batch6_human_correction_root_cause_regression_test.py",
            "focused_integration": "tests/integration/tic_batch6_human_correction_root_cause_regression_test.py",
        },
        "boundary": validation["boundary"],
        "sha256": {"algorithm": "sha256", "self_hash_excluded": True},
    }
    write_canonical_json(base / ROOT_MANIFEST, manifest)
    return base / ROOT_MANIFEST


def main() -> int:
    parser = argparse.ArgumentParser(description="Build TIC Batch 6 offline regressions")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    generate_batch6_artifacts(args.root)
    if args.manifest:
        generate_batch6_manifest(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
