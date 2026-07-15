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
    write_canonical_json,
)

from .evidence_expansion import (
    build_expansion_artifact,
    build_future_excellence_artifact,
    build_unresolved_artifact,
    with_integrity,
)
from .failure_corpus import validate_source_anchors
from .historical_evidence_search import search_historical_human_evidence

BATCH2_CASES = "artifacts/tic_batch2/TRANSLATION_CASES.json"
BATCH4_CORPUS = "artifacts/tic_batch4/HUMAN_CONFIRMED_FAILURE_CORPUS.json"
BATCH4_EXCLUDED = "artifacts/tic_batch4/EXCLUDED_FAILURE_CANDIDATES.json"
BATCH4_ARTIFACT_MANIFEST = "artifacts/tic_batch4/FAILURE_CORPUS_MANIFEST.json"
BATCH4_ROOT_MANIFEST = "manifests/tic_batch4_human_confirmed_failure_corpus_manifest.json"
ARTIFACT_DIR = Path("artifacts/tic_batch5")
EXPANSION_PATH = ARTIFACT_DIR / "HISTORICAL_HUMAN_EVIDENCE_EXPANSION.json"
CORPUS_PATH = ARTIFACT_DIR / "HUMAN_CONFIRMED_FAILURE_CORPUS_V2.json"
UNRESOLVED_PATH = ARTIFACT_DIR / "UNRESOLVED_HUMAN_EVIDENCE.json"
SEARCH_REPORT_PATH = ARTIFACT_DIR / "HUMAN_EVIDENCE_SEARCH_REPORT.json"
STATISTICS_PATH = ARTIFACT_DIR / "FAILURE_CORPUS_V2_STATISTICS.json"
INDEX_PATH = ARTIFACT_DIR / "FAILURE_CASE_INDEX_V2.json"
EXCELLENCE_PATH = ARTIFACT_DIR / "FUTURE_EXCELLENCE_EVIDENCE_CANDIDATES.json"
ARTIFACT_MANIFEST_PATH = ARTIFACT_DIR / "HISTORICAL_HUMAN_EVIDENCE_EXPANSION_MANIFEST.json"
ROOT_MANIFEST = Path("manifests/tic_batch5_historical_human_evidence_expansion_manifest.json")


def _object(root: Path, relative: str) -> dict[str, Any]:
    value = read_json(resolve_project_relative_path(root, relative, must_exist=True))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {relative}")
    return value


def validate_batch1_through_batch4_anchors(root: Path) -> dict[str, str]:
    anchors = validate_source_anchors(root)
    root_manifest = _object(root, BATCH4_ROOT_MANIFEST)
    artifact_path = resolve_project_relative_path(
        root, BATCH4_ARTIFACT_MANIFEST, must_exist=True
    )
    if root_manifest["files"].get(BATCH4_ARTIFACT_MANIFEST) != sha256_file(artifact_path):
        raise ValueError("TIC Batch 4 artifact manifest SHA mismatch")
    artifact_manifest = _object(root, BATCH4_ARTIFACT_MANIFEST)
    for relative in (BATCH4_CORPUS, BATCH4_EXCLUDED):
        actual = sha256_file(resolve_project_relative_path(root, relative, must_exist=True))
        if artifact_manifest["files"].get(relative) != actual:
            raise ValueError(f"TIC Batch 4 input SHA mismatch: {relative}")
        anchors[relative] = actual
    anchors[BATCH4_ARTIFACT_MANIFEST] = sha256_file(artifact_path)
    anchors[BATCH4_ROOT_MANIFEST] = sha256_file(
        resolve_project_relative_path(root, BATCH4_ROOT_MANIFEST, must_exist=True)
    )
    return anchors


def _new_failure(expansion: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    identity = {
        "case_id": expansion["case_id"],
        "alignment_id": expansion["alignment_id"],
        "evidence_id": expansion["evidence_id"],
        "failure_category": expansion["failure_category"],
        "source_sha256": expansion["source_excerpt_sha256"],
        "translation_sha256": expansion["translation_excerpt_sha256"],
    }
    body = {
        "failure_case_id": "TIC-FAIL-B5-" + sha256_bytes(canonical_json_bytes(identity))[:20].upper(),
        "schema_version": "tic.batch5.failure-case.v1",
        "case_id": expansion["case_id"],
        "alignment_id": expansion["alignment_id"],
        "evidence_id": expansion["evidence_id"],
        "source_file": case["source_file"],
        "translation_file": case["translation_file"],
        "source_text": expansion["source_excerpt"],
        "translation_text": expansion["translation_excerpt"],
        "source_start_offset": expansion["source_start_offset"],
        "source_end_offset": expansion["source_end_offset"],
        "translation_start_offset": expansion["translation_start_offset"],
        "translation_end_offset": expansion["translation_end_offset"],
        "source_sha256": expansion["source_excerpt_sha256"],
        "translation_sha256": expansion["translation_excerpt_sha256"],
        "source_overlap": 1.0,
        "translation_overlap": 1.0,
        "alignment_confidence": "high",
        "alignment_type": "one_to_one",
        "failure_category": expansion["failure_category"],
        "failure_subcategory": expansion["failure_subcategory"],
        "severity": expansion["severity"],
        "blocking": expansion["blocking"],
        "observed_error": expansion["observed_error"],
        "expected_semantic_constraint": expansion["expected_semantic_constraint"],
        "human_provenance": expansion["human_provenance"],
        "reviewer_type": "human",
        "review_source": expansion["review_source"],
        "review_reason": expansion["observed_error"],
        "root_cause_status": "not_analyzed",
        "root_cause": None,
        "corrected_translation_status": "not_provided",
        "corrected_translation": None,
        "created_at": "2026-07-16T00:00:00+08:00",
        "source_references": [BATCH2_CASES, expansion["evidence_path"], EXPANSION_PATH.as_posix()],
        "precise_alignment_status": "aligned",
    }
    return with_integrity(body)


def _statistics(
    failures: list[dict[str, Any]], existing_count: int, expansion: list[dict[str, Any]], cases: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    metadata = [cases[item["case_id"]] for item in failures]
    return {
        "schema_version": "tic.batch5.failure-corpus-v2-statistics.v1",
        "total_failure_cases": len(failures),
        "new_failure_cases_added": len(failures) - existing_count,
        "existing_failure_cases_preserved": existing_count,
        "failure_category_counts": dict(sorted(Counter(item["failure_category"] for item in failures).items())),
        "failure_subcategory_counts": dict(sorted(Counter("null" if item["failure_subcategory"] is None else item["failure_subcategory"] for item in failures).items())),
        "severity_counts": dict(sorted(Counter(item["severity"] for item in failures).items())),
        "blocking_count": sum(item["blocking"] for item in failures),
        "nonblocking_count": sum(not item["blocking"] for item in failures),
        "human_evidence_total": len(expansion),
        "human_evidence_precisely_aligned": sum(item["precise_alignment_status"] == "aligned" for item in expansion),
        "human_evidence_unresolved": sum(item["precise_alignment_status"] != "aligned" for item in expansion),
        "root_cause_analyzed_count": sum(item["root_cause_status"] == "human_confirmed" for item in failures),
        "corrected_translation_available_count": sum(item["corrected_translation_status"] == "provided" for item in failures),
        "source_files_count": len({item["source_file"] for item in failures}),
        "translation_files_count": len({item["translation_file"] for item in failures}),
        "providers": sorted({item["provider"] for item in metadata}),
        "models": sorted({item["model"] for item in metadata}),
        "stages": sorted({item["stage"] for item in metadata}),
        "versions": sorted({item["version"] for item in metadata}),
    }


def _index(failures: list[dict[str, Any]], cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    items = []
    for failure in failures:
        case = cases[failure["case_id"]]
        items.append({key: failure[key] for key in ("failure_case_id", "case_id", "alignment_id", "evidence_id", "failure_category", "failure_subcategory", "severity", "blocking", "source_file", "translation_file", "review_source") } | {"provider": case["provider"], "model": case["model"], "stage": case["stage"], "version": case["version"], "precise_alignment_status": failure.get("precise_alignment_status", "aligned")})
    return {"schema_version": "tic.batch5.failure-case-index-v2.v1", "items": items}


def build_batch5_payloads(root: str | Path) -> dict[str, dict[str, Any]]:
    base = Path(root).resolve()
    anchors = validate_batch1_through_batch4_anchors(base)
    cases_payload = _object(base, BATCH2_CASES)
    cases = {item["case_id"]: item for item in cases_payload["translation_cases"]}
    expansion_items, search_report = search_historical_human_evidence(base, cases)
    expansion = build_expansion_artifact(expansion_items)
    unresolved = build_unresolved_artifact(expansion_items)
    excellence = build_future_excellence_artifact()
    batch4 = _object(base, BATCH4_CORPUS)
    failures = list(batch4["failure_cases"])
    seen = {item["evidence_id"] for item in failures}
    for item in expansion_items:
        if not item["usable_for_failure_corpus"]:
            continue
        if item["evidence_id"] in seen:
            raise ValueError(f"duplicate failure evidence: {item['evidence_id']}")
        failures.append(_new_failure(item, cases[item["case_id"]]))
        seen.add(item["evidence_id"])
    corpus_body = {
        "schema_version": "tic.batch5.human-confirmed-failure-corpus-v2.v1",
        "batch": "TIC Batch 5 - Historical Human Evidence Expansion",
        "status": "active_expanded_corpus",
        "source_anchors": anchors,
        "batch4_case_parity_sha256": sha256_bytes(canonical_json_bytes(batch4["failure_cases"])),
        "failure_cases": failures,
        "boundary": {
            "provider_executed": False, "network_requests": 0, "new_translation_generated": False, "historical_translation_modified": False,
            "runtime_modified": False, "provider_modified": False, "prompt_modified": False, "stage11_modified": False, "stage12_modified": False, "golden_corpus_modified": False,
            "batch1_inventory_rebuilt": False, "batch2_cases_rebuilt": False, "batch3_alignment_rebuilt": False, "batch4_failure_corpus_modified": False,
            "historical_human_evidence_expanded": True, "failure_corpus_v2_created": True, "new_failure_cases_added": len(failures) - len(batch4["failure_cases"]),
            "excellence_corpus_created": False, "future_excellence_candidates_created": False,
            "root_cause_analysis_executed": False, "corrected_translation_generated": False, "tic_batch6_started": False,
        },
    }
    corpus = with_integrity(corpus_body)
    statistics = _statistics(failures, len(batch4["failure_cases"]), expansion_items, cases)
    index = _index(failures, cases)
    return {
        EXPANSION_PATH.as_posix(): expansion,
        CORPUS_PATH.as_posix(): corpus,
        UNRESOLVED_PATH.as_posix(): unresolved,
        SEARCH_REPORT_PATH.as_posix(): search_report,
        STATISTICS_PATH.as_posix(): statistics,
        INDEX_PATH.as_posix(): index,
        EXCELLENCE_PATH.as_posix(): excellence,
    }


def generate_batch5_artifacts(root: str | Path) -> dict[str, Path]:
    base = Path(root).resolve(); payloads = build_batch5_payloads(base)
    for relative, payload in payloads.items(): write_canonical_json(base / relative, payload)
    corpus = payloads[CORPUS_PATH.as_posix()]
    manifest = {"schema_version": "tic.batch5.artifact-manifest.v1", "batch": "TIC Batch 5", "source_anchors": corpus["source_anchors"], "files": {relative: sha256_file(base / relative) for relative in payloads}, "boundary": corpus["boundary"], "sha256": {"algorithm": "sha256", "self_hash_excluded": True}}
    write_canonical_json(base / ARTIFACT_MANIFEST_PATH, manifest)
    return {relative: base / relative for relative in (*payloads, ARTIFACT_MANIFEST_PATH.as_posix())}


def generate_batch5_root_manifest(root: str | Path) -> Path:
    base = Path(root).resolve(); files = ["core/translation_intelligence_corpus/historical_evidence_search.py", "core/translation_intelligence_corpus/evidence_expansion.py", "core/translation_intelligence_corpus/failure_corpus_v2.py", EXPANSION_PATH.as_posix(), CORPUS_PATH.as_posix(), UNRESOLVED_PATH.as_posix(), SEARCH_REPORT_PATH.as_posix(), STATISTICS_PATH.as_posix(), INDEX_PATH.as_posix(), EXCELLENCE_PATH.as_posix(), ARTIFACT_MANIFEST_PATH.as_posix(), "docs/translation_intelligence/TIC_BATCH5_HISTORICAL_HUMAN_EVIDENCE_EXPANSION.md", "ntpe_tic_batch5_historical_human_evidence_expansion_test.py", "tests/integration/tic_batch5_historical_human_evidence_expansion_test.py"]
    corpus = _object(base, CORPUS_PATH.as_posix()); manifest = {"schema_version": "tic.batch5.release-manifest.v1", "batch": "TIC Batch 5 - Historical Human Evidence Expansion", "status": "TIC Batch 5 Completed", "next_batch_status": "TIC Batch 6 Not Started", "source_anchors": corpus["source_anchors"], "files": {relative: sha256_file(base / relative) for relative in files}, "tests": {"root": "ntpe_tic_batch5_historical_human_evidence_expansion_test.py", "focused_integration": "tests/integration/tic_batch5_historical_human_evidence_expansion_test.py"}, "boundary": corpus["boundary"], "sha256": {"algorithm": "sha256", "self_hash_excluded": True}}
    write_canonical_json(base / ROOT_MANIFEST, manifest); return base / ROOT_MANIFEST


def main() -> int:
    parser = argparse.ArgumentParser(description="Build TIC Batch 5 evidence expansion")
    parser.add_argument("--root", type=Path, default=Path.cwd()); parser.add_argument("--manifest", action="store_true"); args = parser.parse_args()
    generate_batch5_artifacts(args.root)
    if args.manifest: generate_batch5_root_manifest(args.root)
    return 0


if __name__ == "__main__": raise SystemExit(main())
