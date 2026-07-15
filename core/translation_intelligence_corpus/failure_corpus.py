from __future__ import annotations

import argparse
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

from .failure_index import build_failure_case_index
from .failure_statistics import build_failure_statistics

BATCH1_INVENTORY = "artifacts/tic_batch1/TRANSLATION_CORPUS_INVENTORY.json"
BATCH2_CASES = "artifacts/tic_batch2/TRANSLATION_CASES.json"
BATCH3_INPUTS = (
    "artifacts/tic_batch3/MANUAL_EVIDENCE_INVENTORY.json",
    "artifacts/tic_batch3/MANUAL_EVIDENCE_LINKS.json",
    "artifacts/tic_batch3/TRANSLATION_ALIGNMENT_UNITS.json",
    "artifacts/tic_batch3/TRANSLATION_ALIGNMENT_STATISTICS.json",
    "artifacts/tic_batch3/TRANSLATION_ALIGNMENT_INDEX.json",
)
BATCH3_ARTIFACT_MANIFEST = "artifacts/tic_batch3/TRANSLATION_ALIGNMENT_MANIFEST.json"
BATCH3_ROOT_MANIFEST = "manifests/tic_batch3_manual_evidence_alignment_manifest.json"
ARTIFACT_DIR = Path("artifacts/tic_batch4")
CORPUS_PATH = ARTIFACT_DIR / "HUMAN_CONFIRMED_FAILURE_CORPUS.json"
INDEX_PATH = ARTIFACT_DIR / "FAILURE_CASE_INDEX.json"
STATISTICS_PATH = ARTIFACT_DIR / "FAILURE_CORPUS_STATISTICS.json"
MANIFEST_PATH = ARTIFACT_DIR / "FAILURE_CORPUS_MANIFEST.json"
EXCLUDED_PATH = ARTIFACT_DIR / "EXCLUDED_FAILURE_CANDIDATES.json"
ROOT_MANIFEST = Path("manifests/tic_batch4_human_confirmed_failure_corpus_manifest.json")


def _object(root: Path, relative: str) -> dict[str, Any]:
    path = resolve_project_relative_path(root, relative, must_exist=True)
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {relative}")
    return value


def _integrity(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "algorithm": "sha256",
        "payload_sha256": sha256_bytes(canonical_json_bytes(payload)),
    }


def validate_source_anchors(root: Path) -> dict[str, str]:
    root_manifest = _object(root, BATCH3_ROOT_MANIFEST)
    artifact_manifest_path = resolve_project_relative_path(
        root, BATCH3_ARTIFACT_MANIFEST, must_exist=True
    )
    expected_artifact_sha = root_manifest.get("files", {}).get(BATCH3_ARTIFACT_MANIFEST)
    if expected_artifact_sha != sha256_file(artifact_manifest_path):
        raise ValueError("TIC Batch 3 artifact manifest SHA mismatch")
    artifact_manifest = _object(root, BATCH3_ARTIFACT_MANIFEST)
    anchors: dict[str, str] = {}
    expected_inputs = artifact_manifest.get("input_anchors", {})
    for relative in (BATCH1_INVENTORY, BATCH2_CASES):
        expected = expected_inputs.get(relative)
        actual = sha256_file(resolve_project_relative_path(root, relative, must_exist=True))
        if expected != actual:
            raise ValueError(f"upstream anchor SHA mismatch: {relative}")
        anchors[relative] = actual
    expected_files = artifact_manifest.get("files", {})
    for relative in BATCH3_INPUTS:
        expected = expected_files.get(relative)
        actual = sha256_file(resolve_project_relative_path(root, relative, must_exist=True))
        if expected != actual:
            raise ValueError(f"TIC Batch 3 input SHA mismatch: {relative}")
        anchors[relative] = actual
    anchors[BATCH3_ARTIFACT_MANIFEST] = sha256_file(artifact_manifest_path)
    anchors[BATCH3_ROOT_MANIFEST] = sha256_file(
        resolve_project_relative_path(root, BATCH3_ROOT_MANIFEST, must_exist=True)
    )
    return anchors


def _failure_id(unit: dict[str, Any], evidence_id: str) -> str:
    identity = {
        "case_id": unit["case_id"],
        "alignment_id": unit["alignment_id"],
        "evidence_id": evidence_id,
        "failure_category": unit["failure_category"],
        "source_sha256": unit["source_sha256"],
        "translation_sha256": unit["translation_sha256"],
    }
    return "TIC-FAIL-B4-" + sha256_bytes(canonical_json_bytes(identity))[:20].upper()


def _validate_failure_candidate(
    root: Path,
    unit: dict[str, Any],
    evidence: dict[str, Any],
    link: dict[str, Any],
    case: dict[str, Any],
) -> None:
    if unit["quality_label"] != "human_confirmed_failure":
        raise ValueError("failure unit lacks human_confirmed_failure label")
    if evidence["reviewer_type"] != "human" or not evidence["human_provenance"].get(
        "complete"
    ):
        raise ValueError("failure evidence lacks complete human provenance")
    if not unit["source_text"] or not unit["translation_text"]:
        raise ValueError("failure unit must contain bilateral text")
    if link["source_overlap"] != 1.0 or link["translation_overlap"] != 1.0:
        raise ValueError("failure evidence overlap must be bilateral and exact")
    if unit["anchor_source_overlap"] != 1.0 or unit["anchor_translation_overlap"] != 1.0:
        raise ValueError("failure unit anchor overlap must be bilateral and exact")
    if unit["alignment_confidence"] not in {"exact", "high"}:
        raise ValueError("failure alignment confidence is below high")
    if unit["alignment_type"] in {"source_only", "translation_only", "unresolved"}:
        raise ValueError("unilateral or unresolved unit cannot enter failure corpus")
    if not unit["failure_category"] or unit["failure_category"] not in evidence[
        "defect_categories"
    ]:
        raise ValueError("failure category lacks human evidence")
    if evidence["evidence_id"] not in unit["manual_evidence_ids"]:
        raise ValueError("failure unit lacks evidence reference")
    if unit["alignment_id"] not in link["precise_alignment_unit_ids"]:
        raise ValueError("failure link lacks precise alignment reference")
    if link["precise_alignment_status"] != "aligned" or not link["human_confirmed"]:
        raise ValueError("failure link is not human-confirmed and aligned")
    for name in (
        "source_start_offset",
        "source_end_offset",
        "translation_start_offset",
        "translation_end_offset",
    ):
        if not isinstance(unit[name], int):
            raise ValueError(f"failure unit missing integer offset: {name}")
    if sha256_text(unit["source_text"]) != unit["source_sha256"]:
        raise ValueError("failure source text SHA mismatch")
    if sha256_text(unit["translation_text"]) != unit["translation_sha256"]:
        raise ValueError("failure translation text SHA mismatch")
    if case["source_text"][unit["source_start_offset"] : unit["source_end_offset"]] != unit[
        "source_text"
    ]:
        raise ValueError("failure source offset range mismatch")
    if case["translation_text"][
        unit["translation_start_offset"] : unit["translation_end_offset"]
    ] != unit["translation_text"]:
        raise ValueError("failure translation offset range mismatch")
    source_excerpt = evidence["excerpts"].get("source")
    translation_excerpt = evidence["excerpts"].get("translation")
    if not source_excerpt or not translation_excerpt:
        raise ValueError("failure evidence requires bilateral excerpts")
    if source_excerpt not in unit["source_text"] or translation_excerpt not in unit[
        "translation_text"
    ]:
        raise ValueError("failure excerpts do not exactly match alignment text")
    evidence_path = resolve_project_relative_path(
        root, evidence["evidence_path"], must_exist=True
    )
    if sha256_file(evidence_path) != evidence["evidence_sha256"]:
        raise ValueError("failure evidence artifact SHA mismatch")


def _make_failure_case(
    root: Path,
    unit: dict[str, Any],
    evidence: dict[str, Any],
    link: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    _validate_failure_candidate(root, unit, evidence, link, case)
    review_payload = _object(root, evidence["evidence_path"])
    body: dict[str, Any] = {
        "failure_case_id": _failure_id(unit, evidence["evidence_id"]),
        "schema_version": "tic.batch4.failure-case.v1",
        "case_id": unit["case_id"],
        "alignment_id": unit["alignment_id"],
        "evidence_id": evidence["evidence_id"],
        "source_file": case["source_file"],
        "translation_file": case["translation_file"],
        "source_text": unit["source_text"],
        "translation_text": unit["translation_text"],
        "source_start_offset": unit["source_start_offset"],
        "source_end_offset": unit["source_end_offset"],
        "translation_start_offset": unit["translation_start_offset"],
        "translation_end_offset": unit["translation_end_offset"],
        "source_sha256": unit["source_sha256"],
        "translation_sha256": unit["translation_sha256"],
        "source_overlap": link["source_overlap"],
        "translation_overlap": link["translation_overlap"],
        "alignment_confidence": unit["alignment_confidence"],
        "alignment_type": unit["alignment_type"],
        "failure_category": unit["failure_category"],
        "failure_subcategory": None,
        "severity": "unspecified",
        "blocking": False,
        "human_provenance": evidence["human_provenance"],
        "reviewer_type": evidence["reviewer_type"],
        "review_source": evidence["review_source"],
        "review_reason": review_payload.get("human_finding"),
        "observed_error": "譯文將「理解此情況」的認知主體錯置為鄭泰義；原文中的認知主體是前述遠方的男人。",
        "expected_semantic_constraint": "理解此情況的主體必須保持為前述遠方的男人；不得改為鄭泰義。",
        "root_cause_status": "not_analyzed",
        "root_cause": None,
        "corrected_translation_status": "not_provided",
        "corrected_translation": None,
        "created_at": evidence["created_at"],
        "source_references": [
            BATCH2_CASES,
            BATCH3_INPUTS[0],
            BATCH3_INPUTS[1],
            BATCH3_INPUTS[2],
            evidence["evidence_path"],
        ],
    }
    body["integrity"] = _integrity(body)
    return body


def build_batch4_payloads(root: str | Path) -> dict[str, dict[str, Any]]:
    base = Path(root).resolve()
    anchors = validate_source_anchors(base)
    cases_payload = _object(base, BATCH2_CASES)
    evidence_payload = _object(base, BATCH3_INPUTS[0])
    links_payload = _object(base, BATCH3_INPUTS[1])
    alignments_payload = _object(base, BATCH3_INPUTS[2])
    cases = {item["case_id"]: item for item in cases_payload["translation_cases"]}
    evidence = {item["evidence_id"]: item for item in evidence_payload["items"]}
    links = {item["evidence_id"]: item for item in links_payload["items"]}
    failures: list[dict[str, Any]] = []
    included_evidence: set[str] = set()
    for unit in alignments_payload["alignment_units"]:
        if unit["quality_label"] != "human_confirmed_failure":
            continue
        for evidence_id in unit["manual_evidence_ids"]:
            if evidence_id in included_evidence:
                raise ValueError(f"duplicate failure evidence: {evidence_id}")
            failures.append(
                _make_failure_case(
                    base, unit, evidence[evidence_id], links[evidence_id], cases[unit["case_id"]]
                )
            )
            included_evidence.add(evidence_id)
    excluded: list[dict[str, Any]] = []
    for item in evidence_payload["items"]:
        evidence_id = item["evidence_id"]
        if evidence_id in included_evidence:
            continue
        link = links[evidence_id]
        if item["reviewer_type"] == "automatic":
            reason = "automatic_evidence_not_human_confirmed"
            missing = ["human_reviewer", "complete_human_provenance", "precise_bilateral_alignment"]
            future = "Requires new repository-preserved human review and precise bilateral excerpts."
        elif item["reviewer_type"] == "unknown":
            reason = "unknown_reviewer_and_incomplete_review"
            missing = ["known_human_reviewer", "complete_human_provenance", "human_failure_judgement"]
            future = "Complete a human review before reconsideration."
        else:
            reason = "missing_source_excerpt"
            missing = ["source_excerpt", "precise_bilateral_alignment"]
            future = "Add an exact human source anchor and rebuild alignment in a separately authorized stage."
        excluded.append(
            {
                "evidence_id": evidence_id,
                "case_id": link["case_id"],
                "alignment_id": None,
                "exclusion_reason": reason,
                "missing_requirements": missing,
                "current_status": link["precise_alignment_status"],
                "future_action": future,
            }
        )
    corpus_body: dict[str, Any] = {
        "schema_version": "tic.batch4.human-confirmed-failure-corpus.v1",
        "batch": "TIC Batch 4 - Human-Confirmed Failure Corpus Construction",
        "status": "active_initial_corpus",
        "corpus_scope": "human-confirmed precise bilateral alignments only",
        "source_anchors": anchors,
        "failure_cases": failures,
        "boundary": {
            "provider_executed": False,
            "network_requests": 0,
            "new_translation_generated": False,
            "historical_translation_modified": False,
            "runtime_modified": False,
            "provider_modified": False,
            "prompt_modified": False,
            "stage11_modified": False,
            "stage12_modified": False,
            "golden_corpus_modified": False,
            "batch1_inventory_rebuilt": False,
            "batch2_cases_rebuilt": False,
            "batch3_alignment_rebuilt": False,
            "human_confirmed_failure_corpus_created": True,
            "failure_case_count": len(failures),
            "excellence_corpus_created": False,
            "root_cause_analysis_executed": False,
            "corrected_translation_generated": False,
            "tic_batch5_started": False,
        },
    }
    corpus_body["integrity"] = _integrity(corpus_body)
    excluded_body: dict[str, Any] = {
        "schema_version": "tic.batch4.excluded-failure-candidates.v1",
        "items": excluded,
    }
    excluded_body["integrity"] = _integrity(excluded_body)
    index = build_failure_case_index(failures, cases)
    statistics = build_failure_statistics(
        failures, excluded, evidence_payload["items"], cases
    )
    return {
        CORPUS_PATH.as_posix(): corpus_body,
        INDEX_PATH.as_posix(): index,
        STATISTICS_PATH.as_posix(): statistics,
        EXCLUDED_PATH.as_posix(): excluded_body,
    }


def generate_batch4_artifacts(root: str | Path) -> dict[str, Path]:
    base = Path(root).resolve()
    payloads = build_batch4_payloads(base)
    for relative, payload in payloads.items():
        write_canonical_json(resolve_project_relative_path(base, relative), payload)
    corpus = payloads[CORPUS_PATH.as_posix()]
    manifest = {
        "schema_version": "tic.batch4.failure-corpus-artifact-manifest.v1",
        "batch": "TIC Batch 4",
        "status": "completed",
        "source_anchors": corpus["source_anchors"],
        "files": {
            relative: sha256_file(resolve_project_relative_path(base, relative, must_exist=True))
            for relative in payloads
        },
        "boundary": corpus["boundary"],
        "sha256": {"algorithm": "sha256", "self_hash_excluded": True},
    }
    write_canonical_json(base / MANIFEST_PATH, manifest)
    return {
        **{relative: base / relative for relative in payloads},
        MANIFEST_PATH.as_posix(): base / MANIFEST_PATH,
    }


def generate_batch4_root_manifest(root: str | Path) -> Path:
    base = Path(root).resolve()
    files = [
        "core/translation_intelligence_corpus/failure_corpus.py",
        "core/translation_intelligence_corpus/failure_index.py",
        "core/translation_intelligence_corpus/failure_statistics.py",
        CORPUS_PATH.as_posix(),
        INDEX_PATH.as_posix(),
        STATISTICS_PATH.as_posix(),
        EXCLUDED_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        "docs/translation_intelligence/TIC_BATCH4_HUMAN_CONFIRMED_FAILURE_CORPUS.md",
        "ntpe_tic_batch4_human_confirmed_failure_corpus_test.py",
        "tests/integration/tic_batch4_human_confirmed_failure_corpus_test.py",
    ]
    corpus = _object(base, CORPUS_PATH.as_posix())
    manifest = {
        "schema_version": "tic.batch4.failure-corpus-release-manifest.v1",
        "batch": "TIC Batch 4 - Human-Confirmed Failure Corpus Construction",
        "status": "TIC Batch 4 Completed",
        "next_batch_status": "TIC Batch 5 Not Started",
        "source_anchors": corpus["source_anchors"],
        "files": {
            relative: sha256_file(
                resolve_project_relative_path(base, relative, must_exist=True)
            )
            for relative in files
        },
        "tests": {
            "root": "ntpe_tic_batch4_human_confirmed_failure_corpus_test.py",
            "focused_integration": "tests/integration/tic_batch4_human_confirmed_failure_corpus_test.py",
        },
        "boundary": corpus["boundary"],
        "sha256": {"algorithm": "sha256", "self_hash_excluded": True},
    }
    write_canonical_json(base / ROOT_MANIFEST, manifest)
    return base / ROOT_MANIFEST


def main() -> int:
    parser = argparse.ArgumentParser(description="Build TIC Batch 4 failure corpus")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    generate_batch4_artifacts(args.root)
    if args.manifest:
        generate_batch4_root_manifest(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
