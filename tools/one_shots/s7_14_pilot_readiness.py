"""S7-14 offline pilot-readiness validator.

Static, offline check that the S7-14 readiness package exists and is self-consistent.
It reads only artifacts under the repository; it:
  - imports no production code,
  - performs no translation, no provider/network call,
  - creates no human labels and no pilot data.

Exit code 0 if every REQUIRED check passes, else 1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

REQUIRED_ARTIFACTS = [
    "artifacts/NTPE_S7_14_CALIBRATION_SPLIT_AND_NESTED_CV_POLICY.md",
    "artifacts/NTPE_S7_14_PRIMARY_ENDPOINT_POLICY.md",
    "artifacts/NTPE_S7_14_MISSING_DATA_AND_OUTLIER_POLICY.md",
    "artifacts/NTPE_S7_14_HUMAN_EVALUATOR_REQUIREMENTS.md",
    "artifacts/NTPE_S7_14_REFERENCE_DATA_REQUIREMENTS.md",
    "artifacts/NTPE_S7_14_PILOT_CANDIDATE_REQUIREMENTS.md",
    "artifacts/s7_14_pilot/PILOT_CORPUS_REQUIREMENTS.md",
    "artifacts/s7_14_pilot/BLINDING_REQUIREMENTS.md",
    "artifacts/s7_14_pilot/RANDOMIZATION_REQUIREMENTS.md",
    "artifacts/s7_14_pilot/PROVENANCE_REQUIREMENTS.md",
    "artifacts/s7_14_pilot/PILOT_DEPENDENCY_STATUS.md",
    "artifacts/NTPE_S7_14_CALIBRATION_BLOCKER_STATUS.md",
]


def _read(rel: str) -> str:
    path = REPO / rel
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def check_artifacts_exist() -> tuple[str, str]:
    missing = [p for p in REQUIRED_ARTIFACTS if not (REPO / p).is_file()]
    return ("PASS", "all present") if not missing else ("FAIL", "missing: " + ", ".join(missing))


def check_r1_nested_cv() -> tuple[str, str]:
    text = _read(REQUIRED_ARTIFACTS[0])
    ok = "CLOSED_VERIFIED" in text and "Outer Validation" in text and "Inner CV" in text
    return ("PASS", "R1 boundary defined") if ok else ("FAIL", "R1 boundary incomplete")


def check_r2_primary_endpoint() -> tuple[str, str]:
    text = _read(REQUIRED_ARTIFACTS[1])
    ok = (
        "Aggregate Spearman" in text
        and "FORBIDDEN" in text
        and "Secondary Endpoints" in text
        and "Aggregate Spearman ρ (ONE)" in text
    )
    return ("PASS", "single primary endpoint fixed") if ok else ("FAIL", "primary endpoint ambiguous")


def check_r3_missing_outlier() -> tuple[str, str]:
    text = _read(REQUIRED_ARTIFACTS[2])
    needed = ["MISSING", "ABSTAIN", "INVALID", "Outlier", "predefined", "Sensitivity"]
    ok = all(n in text for n in needed) and "CLOSED_VERIFIED" in text
    return ("PASS", "missing/outlier rules enumerated") if ok else ("FAIL", "rules incomplete")


def check_character_arc_status() -> tuple[str, str]:
    text = _read("artifacts/NTPE_S7_14_CALIBRATION_BLOCKER_STATUS.md")
    if "EXTERNAL_DEPENDENCY" in text:
        return ("WARN", "H02 = EXTERNAL_DEPENDENCY (character-arc annotation needed)")
    if "CLOSED_VERIFIED" in text:
        return ("PASS", "H02 closed")
    return ("FAIL", "H02 status missing or hidden")


def check_blinding() -> tuple[str, str]:
    text = _read("artifacts/s7_14_pilot/BLINDING_REQUIREMENTS.md")
    needed = ["model", "provider", "attempt_number", "condition"]
    ok = all(n in text for n in needed)
    return ("PASS", "blinding contract present") if ok else ("FAIL", "blinding contract incomplete")


def check_randomization() -> tuple[str, str]:
    text = _read("artifacts/s7_14_pilot/RANDOMIZATION_REQUIREMENTS.md")
    ok = "A/B order" in text and "seed" in text.lower() and "counterbalanc" in text.lower()
    return ("PASS", "randomization contract present") if ok else ("FAIL", "randomization incomplete")


def check_provenance() -> tuple[str, str]:
    text = _read("artifacts/s7_14_pilot/PROVENANCE_REQUIREMENTS.md")
    ok = "evaluation_id" in text and "immutable" in text and "derived" in text.lower()
    return ("PASS", "provenance + raw/derived separation present") if ok else ("FAIL", "provenance incomplete")


def check_holdout_protection() -> tuple[str, str]:
    text = _read(REQUIRED_ARTIFACTS[0])
    ok = "one-time final" in text.lower() and "sealed" in text.lower()
    return ("PASS", "holdout sealed + one-time") if ok else ("FAIL", "holdout protection not explicit")


def check_external_dependencies_explicit() -> tuple[str, str]:
    text = _read("artifacts/s7_14_pilot/PILOT_DEPENDENCY_STATUS.md")
    ok = "UNAVAILABLE" in text and "MISSING" in text and "EXTERNAL" in text
    return ("PASS", "human + reference deps explicit") if ok else ("FAIL", "external deps not explicit")


def main() -> int:
    checks = {
        "required_artifacts_exist": check_artifacts_exist(),
        "r1_nested_cv_boundary": check_r1_nested_cv(),
        "r2_primary_endpoint": check_r2_primary_endpoint(),
        "r3_missing_outlier": check_r3_missing_outlier(),
        "h02_character_arc": check_character_arc_status(),
        "blinding": check_blinding(),
        "randomization": check_randomization(),
        "provenance": check_provenance(),
        "holdout_protection": check_holdout_protection(),
        "external_dependencies_explicit": check_external_dependencies_explicit(),
    }
    report = {
        "task": "S7-14",
        "kind": "PILOT_READINESS_VALIDATOR",
        "note": "static/offline only; no human evaluation, no provider, no network",
        "checks": {k: {"status": v[0], "detail": v[1]} for k, v in checks.items()},
        "failures": [k for k, v in checks.items() if v[0] == "FAIL"],
        "warnings": [k for k, v in checks.items() if v[0] == "WARN"],
    }
    report["overall"] = "PASS" if not report["failures"] else "FAIL"
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
