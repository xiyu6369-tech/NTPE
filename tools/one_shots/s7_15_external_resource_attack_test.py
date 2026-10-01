"""S7-15 external-resource synthetic attack tests (offline, deterministic).

Validates that the S7-15 acceptance rules can detect the failure modes in S7-15 section 52.
Synthetic in-memory records only. No humans, no provider, no network, no production imports.

Exit 0 if every EXPECTED detection matches, else 1.
"""

from __future__ import annotations

import json
import sys


def check_evaluator_conflict(record: dict) -> str:
    creator = record.get("creator_id")
    if creator is not None and creator == record.get("evaluator_id"):
        return "FAIL"
    return "OK"


def check_provenance(record: dict) -> str:
    required = ["reference_id", "source_id", "creator_id", "reviewer_id", "reference_class"]
    return "OK" if all(record.get(f) not in (None, "", []) for f in required) else "FAIL"


def check_fake_gold(record: dict) -> str:
    if record.get("reference_class") == "GOLD" and record.get("candidate_origin") == "machine":
        if record.get("human_validated") is not True:
            return "FAIL"
    return "OK"


def check_character_arc(record: dict) -> str:
    if record.get("character_arc_id") in (None, ""):
        return "WARN"
    return "OK"


def check_duplicate_source(records: list[dict]) -> str:
    seen: set[str] = set()
    for r in records:
        h = str(r.get("source_hash"))
        if h in seen:
            return "FAIL"
        seen.add(h)
    return "OK"


def check_primary_endpoint(endpoint) -> str:
    if not isinstance(endpoint, list) or len(endpoint) != 1:
        return "FAIL"
    return "OK"


def check_version_compat(record: dict) -> str:
    if record.get("rubric_version") != record.get("protocol_rubric_version"):
        return "FAIL"
    return "OK"


def main() -> int:
    results = {
        "evaluator_conflict": check_evaluator_conflict({"creator_id": "p1", "evaluator_id": "p1"}),
        "evaluator_clean": check_evaluator_conflict({"creator_id": "p1", "evaluator_id": "e2"}),
        "missing_provenance": check_provenance({"reference_id": "r1", "source_id": "s1"}),
        "provenance_ok": check_provenance(
            {"reference_id": "r1", "source_id": "s1", "creator_id": "t1",
             "reviewer_id": "rv1", "reference_class": "GOLD"}
        ),
        "fake_gold": check_fake_gold(
            {"reference_class": "GOLD", "candidate_origin": "machine", "human_validated": False}
        ),
        "validated_gold": check_fake_gold(
            {"reference_class": "GOLD", "candidate_origin": "machine", "human_validated": True}
        ),
        "character_arc_missing": check_character_arc({}),
        "character_arc_present": check_character_arc({"character_arc_id": "arc_01"}),
        "duplicate_source": check_duplicate_source(
            [{"source_hash": "h1"}, {"source_hash": "h2"}, {"source_hash": "h1"}]
        ),
        "duplicate_clean": check_duplicate_source([{"source_hash": "h1"}, {"source_hash": "h2"}]),
        "endpoint_ambiguous": check_primary_endpoint(["rho", "auc"]),
        "endpoint_single": check_primary_endpoint(["rho"]),
        "version_mismatch": check_version_compat({"rubric_version": "v1.1", "protocol_rubric_version": "v1.0"}),
        "version_match": check_version_compat({"rubric_version": "v1.1", "protocol_rubric_version": "v1.1"}),
    }

    expected = {
        "evaluator_conflict": "FAIL",
        "evaluator_clean": "OK",
        "missing_provenance": "FAIL",
        "provenance_ok": "OK",
        "fake_gold": "FAIL",
        "validated_gold": "OK",
        "character_arc_missing": "WARN",
        "character_arc_present": "OK",
        "duplicate_source": "FAIL",
        "duplicate_clean": "OK",
        "endpoint_ambiguous": "FAIL",
        "endpoint_single": "OK",
        "version_mismatch": "FAIL",
        "version_match": "OK",
    }

    mismatched = {k: results.get(k) for k, v in expected.items() if results.get(k) != v}
    report = {
        "task": "S7-15",
        "kind": "EXTERNAL_RESOURCE_ACQUISITION_ATTACK_TEST",
        "note": "synthetic acceptance-rule validation only; no human data, no real resources",
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
