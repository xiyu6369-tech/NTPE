"""S7-15 external-resource acquisition preflight (offline, deterministic).

Validates that the S7-15 acquisition specifications exist and are self-consistent, and
that the S7-14 methodology policies they depend on are present. Reads artifacts only.

No production imports, no provider/network, no human evaluation, no real translation.
Exit 0 if all REQUIRED checks PASS (WARN allowed for documented external dependencies),
else 1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

REQUIRED_ARTIFACTS = [
    "artifacts/NTPE_S7_15_HUMAN_EVALUATOR_ACQUISITION_SPEC.md",
    "artifacts/NTPE_S7_15_REFERENCE_ACQUISITION_SPEC.md",
    "artifacts/NTPE_S7_15_CHARACTER_ARC_ANNOTATION_SPEC.md",
    "artifacts/NTPE_S7_15_PILOT_CORPUS_ACQUISITION_SPEC.md",
    "artifacts/NTPE_S7_15_CANDIDATE_OUTPUT_ACQUISITION_SPEC.md",
    "artifacts/NTPE_S7_15_EXTERNAL_DATA_INTAKE_SPEC.md",
    "artifacts/s7_15_pilot/PILOT_MANIFEST_SCHEMA.md",
    "artifacts/NTPE_S7_15_EXTERNAL_RESOURCE_DEPENDENCY_STATUS.md",
    "artifacts/s7_15_evaluator/EVALUATOR_INSTRUCTIONS.md",
    "artifacts/s7_15_evaluator/TRAINING_PROTOCOL.md",
    "artifacts/s7_15_evaluator/PRACTICE_PROTOCOL.md",
    "artifacts/s7_15_evaluator/BLINDING_RULES.md",
    "artifacts/s7_15_evaluator/CONFLICT_RULES.md",
    "artifacts/s7_15_evaluator/WITHDRAWAL_RULES.md",
    # S7-14 dependencies
    "artifacts/NTPE_S7_14_PRIMARY_ENDPOINT_POLICY.md",
    "artifacts/NTPE_S7_14_CALIBRATION_SPLIT_AND_NESTED_CV_POLICY.md",
    "artifacts/NTPE_S7_14_MISSING_DATA_AND_OUTLIER_POLICY.md",
]


def _read(rel: str) -> str:
    p = REPO / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def main() -> int:
    missing = [p for p in REQUIRED_ARTIFACTS if not (REPO / p).is_file()]
    eval_spec = _read(REQUIRED_ARTIFACTS[0])
    ref_spec = _read(REQUIRED_ARTIFACTS[1])
    arc_spec = _read(REQUIRED_ARTIFACTS[2])
    corpus_spec = _read(REQUIRED_ARTIFACTS[3])
    cand_spec = _read(REQUIRED_ARTIFACTS[4])
    intake = _read(REQUIRED_ARTIFACTS[5])
    manifest = _read(REQUIRED_ARTIFACTS[6])
    status = _read(REQUIRED_ARTIFACTS[7])
    r1 = _read("artifacts/NTPE_S7_14_CALIBRATION_SPLIT_AND_NESTED_CV_POLICY.md")
    r2 = _read("artifacts/NTPE_S7_14_PRIMARY_ENDPOINT_POLICY.md")
    r3 = _read("artifacts/NTPE_S7_14_MISSING_DATA_AND_OUTLIER_POLICY.md")

    checks = {
        "required_artifacts_exist": ("PASS", "all present") if not missing else ("FAIL", "missing: " + ", ".join(missing)),
        "human_evaluator_package": ("PASS", "schema present") if ("real human" in eval_spec.lower() and "evaluator_id" in eval_spec) else ("FAIL", "evaluator schema incomplete"),
        "reference_provenance": ("PASS", "fields present") if ("reference_id" in ref_spec and "creator_id" in ref_spec and "reviewer_id" in ref_spec) else ("FAIL", "reference provenance incomplete"),
        "reference_role_separation": ("PASS", "creator!=evaluator") if "creator != evaluator" in ref_spec else ("FAIL", "role separation missing"),
        "character_arc_schema": ("PASS", "fields present") if ("character_arc_id" in arc_spec and "annotator_id" in arc_spec and "annotation_version" in arc_spec) else ("FAIL", "arc schema incomplete"),
        "pilot_corpus_manifest": ("PASS", "fields present") if ("sample_id" in corpus_spec and "source_hash" in corpus_spec and "selection_stratum" in corpus_spec) else ("FAIL", "corpus manifest incomplete"),
        "candidate_provenance": ("PASS", "fields present") if ("candidate_id" in cand_spec and "source_hash" in cand_spec and "origin" in cand_spec) else ("FAIL", "candidate provenance incomplete"),
        "blinding": ("PASS", "present") if (REPO / REQUIRED_ARTIFACTS[11]).is_file() and "BLINDING" in _read(REQUIRED_ARTIFACTS[11]).upper() else ("FAIL", "blinding missing"),
        "randomization": ("PASS", "present") if "seed" in _read("artifacts/s7_14_pilot/RANDOMIZATION_REQUIREMENTS.md").lower() else ("WARN", "randomization seed policy not explicit"),
        "provenance_intake": ("PASS", "intake present") if ("Quarantine" in intake and "immutab" in intake.lower()) else ("FAIL", "intake/quarantine/immutability incomplete"),
        "primary_endpoint_unique": ("PASS", "single endpoint") if "Aggregate Spearman ρ (ONE)" in r2 else ("FAIL", "primary endpoint ambiguous"),
        "r1_boundary": ("PASS", "boundary present") if "CLOSED_VERIFIED" in r1 else ("FAIL", "R1 boundary missing"),
        "r3_rules": ("PASS", "rules present") if "CLOSED_VERIFIED" in r3 else ("FAIL", "R3 rules missing"),
        "version_compatibility": ("PASS", "defined") if "version" in intake.lower() and "REVALIDATE" in intake else ("FAIL", "version compatibility not defined"),
        "duplicate_detection": ("PASS", "hash-based") if "source_hash" in corpus_spec and "duplicate" in (intake + corpus_spec).lower() else ("FAIL", "duplicate detection not defined"),
        "leakage_detection": ("PASS", "arc-based signal") if "leakage" in arc_spec.lower() and "cross-split" in arc_spec.lower() else ("FAIL", "leakage detection not defined"),
        "external_dependencies_not_available": ("WARN", "human/reference remain unavailable (expected)") if ("UNAVAILABLE" in status and "MISSING" in status) else ("FAIL", "external dependency status hidden or falsified"),
    }

    failures = [k for k, v in checks.items() if v[0] == "FAIL"]
    warnings = [k for k, v in checks.items() if v[0] == "WARN"]
    report = {
        "task": "S7-15",
        "kind": "EXTERNAL_RESOURCE_ACQUISITION_PREFLIGHT",
        "note": "specification-only offline validation; no human evaluation, no provider, no network",
        "checks": {k: {"status": v[0], "detail": v[1]} for k, v in checks.items()},
        "failures": failures,
        "warnings": warnings,
    }
    report["overall"] = "PASS" if not failures else "FAIL"
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
