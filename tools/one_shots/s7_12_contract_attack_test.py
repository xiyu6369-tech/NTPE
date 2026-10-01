"""S7-12 offline design-contract attack test.

Purpose: statically validate that the Calibration Design v1.1 contract rules
CAN detect the adversarial cases named in S7-12 sections 29/55.

This is CONTRACT/SCHEMA validation only. It:
  - uses synthetic in-memory metadata (no real evaluators, no real references),
  - imports no production code,
  - performs no translation and no provider/network call.

It does NOT establish any production capability and does NOT create human labels.
"""

from __future__ import annotations

import json
import sys


def check_reference_conflict(record: dict) -> str:
    """v1.1 section 16: reference creator must differ from primary evaluator."""
    creator = record.get("reference_creator_id")
    evaluators = set(record.get("evaluator_ids", []))
    if creator is not None and creator in evaluators:
        return "CONFLICT"
    return "OK"


def check_chapter_leakage(record: dict) -> str:
    """v1.1 sections 6.2/15: a chapter must not cross splits."""
    seen: dict[str, str] = {}
    for split in ("calibration", "validation", "holdout"):
        for chapter in record.get(split, []):
            if chapter in seen and seen[chapter] != split:
                return "INVALID_SPLIT"
            seen[chapter] = split
    return "OK"


def check_candidate_leakage(record: dict) -> str:
    """v1.1 section 16.3: same candidate text must not appear in two splits."""
    seen: dict[str, str] = {}
    for split in ("calibration", "validation", "holdout"):
        for candidate in record.get(split, []):
            if candidate in seen and seen[candidate] != split:
                return "INVALID"
            seen[candidate] = split
    return "OK"


def classify_target(target: dict) -> str:
    """v1.1 section 26: uncalibrated constants must not be treated as validated."""
    value = target.get("value")
    status = target.get("status")
    if value in (80, 65) and status not in ("PRE-REGISTERED TARGET", "UNCALIBRATED"):
        return "UNCALIBRATED"
    return status or "TBD"


def main() -> int:
    results = {
        "test_1_reference_conflict": check_reference_conflict(
            {
                "reference_creator_id": "translator_01",
                "evaluator_ids": ["translator_01", "evaluator_02"],
            }
        ),
        "test_1b_reference_clean": check_reference_conflict(
            {
                "reference_creator_id": "translator_01",
                "evaluator_ids": ["evaluator_02", "evaluator_03"],
            }
        ),
        "test_2_chapter_leakage": check_chapter_leakage(
            {"calibration": ["ch01", "ch02"], "validation": ["ch03"], "holdout": ["ch02"]}
        ),
        "test_2b_split_clean": check_chapter_leakage(
            {"calibration": ["ch01", "ch02"], "validation": ["ch03"], "holdout": ["ch04"]}
        ),
        "test_3_candidate_leakage": check_candidate_leakage(
            {"calibration": ["cand_a", "cand_b"], "validation": [], "holdout": ["cand_b"]}
        ),
        "test_3b_candidate_clean": check_candidate_leakage(
            {"calibration": ["cand_a"], "validation": ["cand_b"], "holdout": ["cand_c"]}
        ),
        "test_4_target_80": classify_target({"name": "success_threshold", "value": 80}),
        "test_4b_target_kappa": classify_target(
            {"name": "kappa_w", "value": 0.60, "status": "PRE-REGISTERED TARGET"}
        ),
    }

    expected = {
        "test_1_reference_conflict": "CONFLICT",
        "test_1b_reference_clean": "OK",
        "test_2_chapter_leakage": "INVALID_SPLIT",
        "test_2b_split_clean": "OK",
        "test_3_candidate_leakage": "INVALID",
        "test_3b_candidate_clean": "OK",
        "test_4_target_80": "UNCALIBRATED",
        "test_4b_target_kappa": "PRE-REGISTERED TARGET",
    }

    passed = sum(1 for k, v in expected.items() if results.get(k) == v)
    total = len(expected)
    report = {
        "task": "S7-12",
        "kind": "DESIGN_CONTRACT_ATTACK_TEST",
        "note": "synthetic contract/schema validation only; no human evaluation, no production capability",
        "results": results,
        "expected": expected,
        "passed": passed,
        "total": total,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
