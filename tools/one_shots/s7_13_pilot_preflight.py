"""S7-13 offline pilot-protocol preflight / attack tests.

Purpose: statically validate that the pilot PRESENTATION and DATA-INTEGRITY
contracts from Calibration Design v1.1 can detect the adversarial conditions
named in S7-13 sections 22-23, 44, 49 and 74.

This is PRESENTATION/SCHEMA validation ONLY. It:
  - uses synthetic in-memory records (no real evaluators, no real candidates),
  - imports no production code,
  - performs no translation and no provider/network call,
  - creates NO human labels and NO pilot data.

It does NOT establish any production capability and does NOT execute a pilot.
"""

from __future__ import annotations

import json
import sys

FORBIDDEN_PRESENTATION_FIELDS = {
    "model",
    "provider",
    "attempt_number",
    "condition",
    "gold_silver_bronze",
    "prompt_version",
    "ps03_score",
    "production_designation",
}
MISSING_CODES = {"missing", "abstain", "invalid"}


def check_blinding(presentation: dict) -> str:
    """v1.1 section 16.4 / S7-13 section 22: hidden metadata must not leak."""
    exposed = FORBIDDEN_PRESENTATION_FIELDS.intersection(presentation.keys())
    return "BLINDING_LEAK:" + ",".join(sorted(exposed)) if exposed else "OK"


def check_reference_conflict(record: dict) -> str:
    """v1.1 section 16 / S7-13 section 21: creator must not be the evaluator."""
    creator = record.get("reference_creator_id")
    evaluators = set(record.get("evaluator_ids", []))
    if creator is not None and creator in evaluators:
        return "INVALID"
    return "OK"


def check_duplicate_candidate(assignment: dict) -> str:
    """S7-13 section 18/49: same candidate must not be duplicated unfairly."""
    candidates = assignment.get("candidate_ids", [])
    if len(candidates) != len(set(candidates)):
        return "DUPLICATE_DETECTED"
    return "OK"


def check_order_balance(pairs: list[dict]) -> str:
    """S7-13 section 23/74: A-first and B-first must be counterbalanced."""
    a_first = sum(1 for p in pairs if p.get("presented_first") == "A")
    b_first = sum(1 for p in pairs if p.get("presented_first") == "B")
    if a_first == 0 or b_first == 0:
        return "ORDER_IMBALANCE"
    if abs(a_first - b_first) > max(1, 0.25 * (a_first + b_first)):
        return "ORDER_IMBALANCE"
    return "OK"


def check_missing_preserved(rows: list[dict]) -> str:
    """S7-13 section 44: missing/abstain/invalid must be retained as raw states."""
    for row in rows:
        code = row.get("response")
        if code in MISSING_CODES and row.get("value") is not None:
            return "SILENT_FILL"
    return "OK"


def main() -> int:
    results = {
        "blinding_leak": check_blinding(
            {"source": "s1", "candidate": "c1", "model": "nvidia", "attempt_number": 2}
        ),
        "blinding_clean": check_blinding(
            {"source": "s1", "candidate_text": "..."}
        ),
        "reference_conflict": check_reference_conflict(
            {"reference_creator_id": "translator_01", "evaluator_ids": ["translator_01", "evaluator_02"]}
        ),
        "reference_clean": check_reference_conflict(
            {"reference_creator_id": "translator_01", "evaluator_ids": ["evaluator_02"]}
        ),
        "duplicate_candidate": check_duplicate_candidate({"candidate_ids": ["c1", "c2", "c1"]}),
        "duplicate_clean": check_duplicate_candidate({"candidate_ids": ["c1", "c2", "c3"]}),
        "order_imbalance": check_order_balance(
            [{"presented_first": "A"}, {"presented_first": "A"}, {"presented_first": "A"}]
        ),
        "order_balanced": check_order_balance(
            [{"presented_first": "A"}, {"presented_first": "B"}, {"presented_first": "B"}, {"presented_first": "A"}]
        ),
        "missing_silent_fill": check_missing_preserved(
            [{"response": "abstain", "value": 4}]
        ),
        "missing_preserved": check_missing_preserved(
            [{"response": "abstain", "value": None}, {"response": "ok", "value": 5}]
        ),
    }

    expected = {
        "blinding_leak": "BLINDING_LEAK:attempt_number,model",
        "blinding_clean": "OK",
        "reference_conflict": "INVALID",
        "reference_clean": "OK",
        "duplicate_candidate": "DUPLICATE_DETECTED",
        "duplicate_clean": "OK",
        "order_imbalance": "ORDER_IMBALANCE",
        "order_balanced": "OK",
        "missing_silent_fill": "SILENT_FILL",
        "missing_preserved": "OK",
    }

    passed = sum(1 for k, v in expected.items() if results.get(k) == v)
    total = len(expected)
    report = {
        "task": "S7-13",
        "kind": "PILOT_PROTOCOL_PREFLIGHT_ATTACK_TEST",
        "note": "synthetic presentation/schema validation only; no human evaluation, no pilot data, no production capability",
        "results": results,
        "expected": expected,
        "passed": passed,
        "total": total,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
