"""Artifact and report builders for the TIC Batch 7 offline quality gate."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

from core.shared.evidence import canonical_json_bytes, read_json, sha256_bytes, sha256_file, write_canonical_json

from .correction_records import with_integrity
from .offline_quality_gate import (
    APPROVALS_PATH, REGRESSIONS_PATH, ROOT, _default_context,
    evaluate_translation_candidate, validate_batch1_through_batch61_anchors,
    validate_untrusted_regression_records,
)


ARTIFACT_DIR = Path("artifacts/tic_batch7")
FIXTURES_PATH = ARTIFACT_DIR / "OFFLINE_QUALITY_GATE_FIXTURES.json"
GATE_PATH = ARTIFACT_DIR / "OFFLINE_TRANSLATION_QUALITY_GATE.json"
VALIDATION_PATH = ARTIFACT_DIR / "OFFLINE_QUALITY_GATE_VALIDATION.json"
INDEX_PATH = ARTIFACT_DIR / "OFFLINE_QUALITY_GATE_INDEX.json"
STATISTICS_PATH = ARTIFACT_DIR / "TIC_BATCH7_STATISTICS.json"
PERFORMANCE_PATH = ARTIFACT_DIR / "OFFLINE_QUALITY_GATE_PERFORMANCE.json"
ROOT_MANIFEST = Path("manifests/tic_batch7_offline_translation_quality_gate_manifest.json")
RELEASE_DOCUMENT = Path("docs/translation_intelligence/TIC_BATCH7_OFFLINE_TRANSLATION_QUALITY_GATE.md")
ROOT_TEST = Path("ntpe_tic_batch7_offline_translation_quality_gate_test.py")
FOCUSED_TEST = Path("tests/integration/tic_batch7_offline_translation_quality_gate_test.py")
PERFORMANCE_TEST = Path("tests/performance/tic_batch7_offline_quality_gate_benchmark.py")


def quality_gate_result_payload(result: Any) -> dict[str, Any]:
    """Return a canonical-JSON-compatible copy of an immutable result."""
    return result.as_dict()


def _fixture_payloads(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    context = _default_context()
    by_category = {item["category"]: item for item in context.regressions}
    subject = by_category["subject_reference_shift"]
    lexical = by_category["lexical_choice"]
    fixtures = [
        {"fixture_id": "B7-SUBJECT-BAD", "source_text": subject["source_text"], "translation_text": subject["bad_translation"], "applicable_regression_ids": [subject["regression_id"]], "expected_status": "fail", "kind": "historical_bad"},
        {"fixture_id": "B7-SUBJECT-APPROVED", "source_text": subject["source_text"], "translation_text": subject["approved_translation"], "applicable_regression_ids": [subject["regression_id"]], "expected_status": "pass", "kind": "human_approved"},
        {"fixture_id": "B7-SUBJECT-UNRELATED", "source_text": subject["source_text"], "translation_text": "完全無關的固定測試句子。", "applicable_regression_ids": [subject["regression_id"]], "expected_status": "fail", "kind": "unrelated_translation"},
        {"fixture_id": "B7-LEXICAL-BAD", "source_text": lexical["source_text"], "translation_text": lexical["bad_translation"], "applicable_regression_ids": [lexical["regression_id"]], "expected_status": "fail", "kind": "historical_bad"},
        {"fixture_id": "B7-LEXICAL-APPROVED", "source_text": lexical["source_text"], "translation_text": lexical["approved_translation"], "applicable_regression_ids": [lexical["regression_id"]], "expected_status": "pass", "kind": "human_approved"},
        {"fixture_id": "B7-LEXICAL-UNRELATED", "source_text": lexical["source_text"], "translation_text": "完全無關的人。", "applicable_regression_ids": [lexical["regression_id"]], "expected_status": "fail", "kind": "unrelated_translation"},
        {"fixture_id": "B7-NOT-APPLICABLE", "source_text": "이 문장은 고정 회귀 사례와 관련이 없다.", "translation_text": "這是完全無關的譯文。", "applicable_regression_ids": None, "expected_status": "not_applicable", "kind": "unrelated_source"},
        {"fixture_id": "B7-EMPTY-TRANSLATION", "source_text": subject["source_text"], "translation_text": "", "applicable_regression_ids": [subject["regression_id"]], "expected_status": "invalid_input", "kind": "invalid_input"},
        {"fixture_id": "B7-TAMPERED-REGRESSION", "regression_id": subject["regression_id"], "tamper": "approved_translation_sha256", "tampered_value": "0" * 64, "expected_status": "invalid_input", "kind": "tampered_regression"},
    ]
    results: list[dict[str, Any]] = []
    for fixture in fixtures[:-1]:
        ids = fixture["applicable_regression_ids"]
        result = evaluate_translation_candidate(
            source_text=fixture["source_text"], translation_text=fixture["translation_text"],
            applicable_regression_ids=tuple(ids) if ids is not None else None,
            candidate_id=fixture["fixture_id"],
        )
        if result.gate_status != fixture["expected_status"]:
            raise ValueError(f"fixture status mismatch: {fixture['fixture_id']}")
        results.append({"fixture_id": fixture["fixture_id"], "kind": fixture["kind"], **quality_gate_result_payload(result)})
    regression_payload = read_json(root / REGRESSIONS_PATH)
    approvals_payload = read_json(root / APPROVALS_PATH)
    tampered = deepcopy(regression_payload["items"])
    tampered[0]["approved_translation_sha256"] = "0" * 64
    valid, reasons = validate_untrusted_regression_records(regressions=tuple(tampered), approvals=tuple(approvals_payload["items"]))
    if valid:
        raise ValueError("tampered regression was not rejected")
    results.append({"fixture_id": fixtures[-1]["fixture_id"], "kind": "tampered_regression", "gate_status": "invalid_input", "quality_candidate_allowed": False, "review_ready": False, "regression_safe": False, "failure_reasons": list(reasons), "provider_executed": False, "network_requests": 0, "disk_writes": 0})
    return (
        {"schema_version": "tic.batch7.offline-quality-gate-fixtures.v1", "items": fixtures},
        {"schema_version": "tic.batch7.offline-quality-gate-validation-results.v1", "items": results},
    )


def build_batch7_payloads(root: str | Path = ROOT) -> dict[str, dict[str, Any]]:
    base = Path(root).resolve()
    anchors = validate_batch1_through_batch61_anchors(base)
    context = _default_context()
    fixtures, raw_validation = _fixture_payloads(base)
    results = raw_validation["items"]
    statuses = [item["gate_status"] for item in results]
    gate_id = "TIC-GATE-B7-" + sha256_bytes(canonical_json_bytes({"regressions": [item["regression_id"] for item in context.regressions], "anchors": anchors}))[:20].upper()
    contracts = []
    index_items = []
    for item in context.regressions:
        contract = {
            "regression_id": item["regression_id"], "failure_case_id": item["failure_case_id"],
            "category": item["category"], "source_sha256": item["source_sha256"],
            "source_excerpt": item["source_text"], "case_id": item["case_id"],
            "alignment_id": item["alignment_id"], "applicability_type": item["applicability_type"],
            "global_rule": False,
        }
        contracts.append(contract)
        index_items.append({
            "regression_id": item["regression_id"], "failure_case_id": item["failure_case_id"],
            "category": item["category"], "case_id": item["case_id"], "alignment_id": item["alignment_id"],
            "evaluation_type": item["evaluation_type"], "regression_gate_blocking": item["regression_gate_blocking"],
            "defect_blocking": item["defect_blocking"], "applicability_type": item["applicability_type"],
            "gate_status": "active",
        })
    gate = with_integrity({
        "schema_version": "tic.batch7.offline-translation-quality-gate.v1",
        "batch": "TIC Batch 7 - Offline Translation Quality Gate Integration",
        "gate_id": gate_id, "status": "offline_active",
        "active_regression_anchors": {item["regression_id"]: item["integrity"]["payload_sha256"] for item in context.regressions},
        "applicability_contracts": contracts,
        "gate_rules": {"pass_requires_all_applicable": True, "not_applicable_is_pass": False, "invalid_input_fail_closed": True, "automatic_approval": False},
        "blocking_semantics": {"defect_blocking": "original Failure Corpus metadata", "regression_gate_blocking": "blocks quality candidate when this fixed regression fails"},
        "provider_boundary": {"provider_connected": False, "provider_requests": 0, "network_requests": 0},
        "production_boundary": {"production_connected": False, "runtime_connected": False, "prompt_connected": False, "qa_engine_connected": False},
    })
    validation = {
        "schema_version": "tic.batch7.offline-quality-gate-validation.v1",
        "fixtures_evaluated": len(results), "pass_count": statuses.count("pass"), "fail_count": statuses.count("fail"),
        "not_applicable_count": statuses.count("not_applicable"), "invalid_input_count": statuses.count("invalid_input"),
        "insufficient_evidence_count": statuses.count("insufficient_evidence"),
        "historical_bad_fail_count": sum(item["kind"] == "historical_bad" and item["gate_status"] == "fail" for item in results),
        "approved_pass_count": sum(item["kind"] == "human_approved" and item["gate_status"] == "pass" for item in results),
        "unrelated_not_accepted_count": sum(item["kind"] in {"unrelated_translation", "unrelated_source"} and item["gate_status"] != "pass" for item in results),
        "provider_requests": 0, "network_requests": 0, "disk_writes": 0, "runtime_stages": 0,
        "deterministic": build_determinism_probe(context), "gate_pass": True,
        "validation_results": results, "source_anchors": anchors,
    }
    statistics = {
        "schema_version": "tic.batch7.statistics.v1", "active_regressions_loaded": len(context.regressions),
        "gate_fixtures": len(results), "gate_passes": statuses.count("pass"), "gate_failures": statuses.count("fail"),
        "not_applicable": statuses.count("not_applicable"), "invalid_inputs": statuses.count("invalid_input"),
        "insufficient_evidence": statuses.count("insufficient_evidence"),
        "historical_bad_fail_count": validation["historical_bad_fail_count"], "human_approved_pass_count": validation["approved_pass_count"],
        "unrelated_candidate_rejected_count": validation["unrelated_not_accepted_count"],
        "production_integrations": 0, "provider_integrations": 0, "runtime_integrations": 0, "prompt_integrations": 0,
        "quality_candidates_allowed": statuses.count("pass"), "quality_candidates_blocked": len(results) - statuses.count("pass"),
    }
    return {
        FIXTURES_PATH.as_posix(): fixtures, GATE_PATH.as_posix(): gate,
        VALIDATION_PATH.as_posix(): validation,
        INDEX_PATH.as_posix(): {"schema_version": "tic.batch7.offline-quality-gate-index.v1", "items": index_items},
        STATISTICS_PATH.as_posix(): statistics,
    }


def build_determinism_probe(context: Any) -> bool:
    item = context.regressions[0]
    kwargs = {"source_text": item["source_text"], "translation_text": item["approved_translation"], "applicable_regression_ids": (item["regression_id"],), "candidate_id": "B7-DETERMINISM-PROBE"}
    return evaluate_translation_candidate(**kwargs).as_dict() == evaluate_translation_candidate(**kwargs).as_dict()


def generate_batch7_artifacts(root: str | Path = ROOT) -> dict[str, Path]:
    base = Path(root).resolve()
    payloads = build_batch7_payloads(base)
    for relative, payload in payloads.items():
        write_canonical_json(base / relative, payload)
    return {relative: base / relative for relative in payloads}


def generate_batch7_manifest(root: str | Path = ROOT) -> Path:
    base = Path(root).resolve()
    validation = read_json(base / VALIDATION_PATH)
    files = [
        "core/translation_intelligence_corpus/quality_gate_models.py", "core/translation_intelligence_corpus/offline_quality_gate.py",
        "core/translation_intelligence_corpus/quality_gate_report.py", FIXTURES_PATH.as_posix(), GATE_PATH.as_posix(),
        VALIDATION_PATH.as_posix(), INDEX_PATH.as_posix(), STATISTICS_PATH.as_posix(), PERFORMANCE_PATH.as_posix(),
        ROOT_TEST.as_posix(), FOCUSED_TEST.as_posix(), PERFORMANCE_TEST.as_posix(), RELEASE_DOCUMENT.as_posix(),
    ]
    manifest = {
        "schema_version": "tic.batch7.release-manifest.v1", "batch": "TIC Batch 7 - Offline Translation Quality Gate Integration",
        "status": "TIC Batch 7 Completed", "next_batch_status": "TIC Batch 8 Not Started",
        "source_anchors": validation["source_anchors"], "files": {item: sha256_file(base / item) for item in files},
        "tests": {"root": ROOT_TEST.as_posix(), "focused_integration": FOCUSED_TEST.as_posix(), "performance": PERFORMANCE_TEST.as_posix()},
        "boundary": {"provider_executed": False, "network_requests": 0, "new_translation_generated": False, "historical_translation_modified": False, "runtime_modified": False, "provider_modified": False, "prompt_modified": False, "qa_engine_modified": False, "stage11_modified": False, "stage12_modified": False, "batch61_artifacts_modified": False, "offline_quality_gate_created": True, "active_regressions_loaded": 2, "production_gate_connected": False, "provider_requests_added": 0, "prompt_tokens_added": 0, "disk_writes_added": 0, "runtime_stages_added": 0, "production_fix_applied": False, "translation_quality_improved": False, "offline_regression_gate_available": True, "tic_batch8_started": False},
        "sha256": {"algorithm": "sha256", "self_hash_excluded": True},
    }
    write_canonical_json(base / ROOT_MANIFEST, manifest)
    return base / ROOT_MANIFEST


def main() -> int:
    parser = argparse.ArgumentParser(description="Build TIC Batch 7 offline quality gate artifacts")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    generate_batch7_artifacts(args.root)
    if args.manifest:
        generate_batch7_manifest(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
