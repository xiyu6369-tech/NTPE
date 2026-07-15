from __future__ import annotations

from typing import Any

from core.shared.evidence import canonical_json_bytes, sha256_bytes


def with_integrity(payload: dict[str, Any]) -> dict[str, Any]:
    body = dict(payload)
    body["integrity"] = {
        "algorithm": "sha256",
        "payload_sha256": sha256_bytes(canonical_json_bytes(payload)),
    }
    return body


def build_expansion_artifact(items: list[dict[str, Any]]) -> dict[str, Any]:
    return with_integrity(
        {
            "schema_version": "tic.batch5.historical-human-evidence-expansion.v1",
            "batch": "TIC Batch 5 - Historical Human Evidence Expansion",
            "items": items,
        }
    )


def build_unresolved_artifact(items: list[dict[str, Any]]) -> dict[str, Any]:
    unresolved = []
    for item in items:
        if item["precise_alignment_status"] == "aligned":
            continue
        missing = []
        if item["source_excerpt"] is None:
            missing.extend(["exact_source_excerpt", "source_offsets", "source_excerpt_sha256"])
        if item["translation_excerpt"] is None:
            missing.extend(
                ["exact_translation_excerpt", "translation_offsets", "translation_excerpt_sha256"]
            )
        missing.append("precise_bilateral_alignment")
        unresolved.append(
            {
                "evidence_id": item["evidence_id"],
                "case_id": item["case_id"],
                "evidence_path": item["evidence_path"],
                "human_provenance": item["human_provenance"],
                "missing_requirements": missing,
                "search_attempts": [item["search_method"]],
                "candidate_source_files": [item["source_file"]],
                "candidate_translation_files": [item["translation_file"]],
                "ambiguity_reason": item["ambiguity_reason"],
                "current_status": "linked_but_not_aligned",
                "future_action": "Obtain a repository-preserved literal human source/translation anchor; do not infer text.",
            }
        )
    return with_integrity(
        {
            "schema_version": "tic.batch5.unresolved-human-evidence.v1",
            "items": unresolved,
        }
    )


def build_future_excellence_artifact() -> dict[str, Any]:
    return with_integrity(
        {
            "schema_version": "tic.batch5.future-excellence-evidence-candidates.v1",
            "items": [],
            "excellence_corpus_created": False,
            "note": "No provenance-complete, precisely bilateral human praise evidence was found.",
        }
    )
