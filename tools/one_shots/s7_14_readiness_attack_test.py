"""S7-14 offline readiness attack tests.

Validates that the S7-14 policy rules can detect, statically, the failure modes named
in S7-14 section 49. Uses synthetic in-memory records only. No humans, no provider,
no network, no production imports.

Exit code 0 if every EXPECTED detection matches, else 1.
"""

from __future__ import annotations

import json
import sys


def check_primary_endpoint(endpoint: list[str]) -> str:
    """R2: exactly one primary endpoint; a disjunction is invalid."""
    if not isinstance(endpoint, list) or len(endpoint) != 1:
        return "FAIL"
    return "OK"


def check_layer_disjoint(record: dict) -> str:
    """R1: tuning samples and validation samples must be disjoint."""
    tuning = set(record.get("tuning_sample_ids", []))
    validation = set(record.get("validation_sample_ids", []))
    if tuning & validation:
        return "FAIL"
    return "OK"


def check_holdout_untouched(record: dict) -> str:
    """R1: holdout must never appear in tuning/selection."""
    holdout = set(record.get("holdout_sample_ids", []))
    used = set(record.get("tuning_sample_ids", [])) | set(record.get("selection_sample_ids", []))
    if holdout & used:
        return "FAIL"
    return "OK"


def check_process_rule(record: dict) -> str:
    """R3: missing/outlier/exclusion rules must be predefined and outcome-independent."""
    if record.get("exclusion_rule") in (None, "", "post_hoc"):
        return "FAIL"
    if record.get("rule_predefined") is not True:
        return "FAIL"
    return "OK"


def check_reference_role(record: dict) -> str:
    """H08/R: reference creator must not be the evaluator."""
    creator = record.get("reference_creator_id")
    if creator is not None and creator in set(record.get("evaluator_ids", [])):
        return "FAIL"
    return "OK"


def check_character_arc(record: dict) -> str:
    """H02: arc grouping unset is a WARN/MEDIUM, not a hard fail."""
    if not record.get("character_arc_grouping"):
        return "WARN"
    return "OK"


def main() -> int:
    results = {
        "endpoint_disjunction": check_primary_endpoint(["rho", "auc"]),
        "endpoint_single": check_primary_endpoint(["rho"]),
        "validation_leakage": check_layer_disjoint(
            {"tuning_sample_ids": ["s1", "s2"], "validation_sample_ids": ["s2", "s3"]}
        ),
        "validation_clean": check_layer_disjoint(
            {"tuning_sample_ids": ["s1", "s2"], "validation_sample_ids": ["s3", "s4"]}
        ),
        "holdout_leakage": check_holdout_untouched(
            {"holdout_sample_ids": ["h1"], "tuning_sample_ids": ["h1"]}
        ),
        "holdout_clean": check_holdout_untouched(
            {"holdout_sample_ids": ["h1"], "tuning_sample_ids": ["s1"]}
        ),
        "missing_posthoc_exclusion": check_process_rule(
            {"exclusion_rule": "post_hoc", "rule_predefined": False}
        ),
        "missing_predefined": check_process_rule(
            {"exclusion_rule": "INATTENTIVE_ONLY", "rule_predefined": True}
        ),
        "reference_conflict": check_reference_role(
            {"reference_creator_id": "t1", "evaluator_ids": ["t1", "e2"]}
        ),
        "reference_clean": check_reference_role(
            {"reference_creator_id": "t1", "evaluator_ids": ["e2"]}
        ),
        "character_arc_unset": check_character_arc({}),
        "character_arc_set": check_character_arc({"character_arc_grouping": "arc_01"}),
    }

    expected = {
        "endpoint_disjunction": "FAIL",
        "endpoint_single": "OK",
        "validation_leakage": "FAIL",
        "validation_clean": "OK",
        "holdout_leakage": "FAIL",
        "holdout_clean": "OK",
        "missing_posthoc_exclusion": "FAIL",
        "missing_predefined": "OK",
        "reference_conflict": "FAIL",
        "reference_clean": "OK",
        "character_arc_unset": "WARN",
        "character_arc_set": "OK",
    }

    mismatched = {k: results.get(k) for k, v in expected.items() if results.get(k) != v}
    report = {
        "task": "S7-14",
        "kind": "READINESS_ATTACK_TEST",
        "note": "synthetic policy-rule validation only; no human evaluation, no pilot data",
        "results": results,
        "expected": expected,
        "mismatched": mismatched,
        "passed": len(expected) - len(mismatched),
        "total": len(expected),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not mismatched else 1


if __name__ == "__main__":
    sys.exit(main())
