from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _overlap(text: str, excerpt: str | None) -> tuple[float, int | None]:
    if not excerpt:
        return 0.0, None
    offset = text.find(excerpt)
    return (1.0, offset) if offset >= 0 else (0.0, None)


def link_evidence(evidence: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Any]:
    candidates: list[tuple[dict[str, Any], str, str]] = []
    source_excerpt = evidence.get("excerpts", {}).get("source")
    translation_excerpt = evidence.get("excerpts", {}).get("translation")
    for case in cases:
        exact_translation = evidence.get("referenced_translation_path") == case.get("translation_file")
        exact_source = evidence.get("referenced_source_path") == case.get("source_file")
        source_overlap, _ = _overlap(case.get("source_text", ""), source_excerpt)
        translation_overlap, _ = _overlap(case.get("translation_text", ""), translation_excerpt)
        if exact_translation:
            candidates.append((case, "exact_file_reference", "translation_path"))
        elif exact_source and (source_overlap or translation_overlap):
            candidates.append((case, "exact_excerpt_match", "source_path_and_excerpt"))
        elif source_overlap and translation_overlap:
            candidates.append((case, "exact_excerpt_match", "source_and_translation_excerpt"))

    preferred_ids = set(evidence.get("referenced_case_ids", []))
    if preferred_ids:
        candidates = [candidate for candidate in candidates if candidate[0]["case_id"] in preferred_ids]
    unique = {candidate[0]["case_id"]: candidate for candidate in candidates}
    if len(unique) != 1:
        case = None
        link_type = "ambiguous" if unique else "unlinked"
        confidence = "unresolved"
        method = "multiple_candidates" if unique else "no_exact_candidate"
        ambiguity = f"{len(unique)} exact candidates" if unique else "no exact file or excerpt match"
    else:
        case, link_type, method = next(iter(unique.values()))
        confidence = "exact"
        ambiguity = None

    case_id = case["case_id"] if case else None
    source_text = case.get("source_text", "") if case else ""
    translation_text = case.get("translation_text", "") if case else ""
    source_overlap, source_offset = _overlap(source_text, source_excerpt)
    translation_overlap, translation_offset = _overlap(translation_text, translation_excerpt)
    provenance_complete = bool(evidence.get("human_provenance", {}).get("complete"))
    human_confirmed = bool(
        case
        and evidence.get("reviewer_type") == "human"
        and provenance_complete
        and (link_type in {"exact_file_reference", "exact_sha_reference", "exact_excerpt_match", "offset_match"})
    )
    identity = f"{evidence['evidence_id']}|{case_id or 'UNLINKED'}|{link_type}|{method}"
    return {
        "link_id": "TIC-LINK-B3-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20].upper(),
        "evidence_id": evidence["evidence_id"],
        "case_id": case_id,
        "link_type": link_type,
        "link_confidence": confidence,
        "link_method": method,
        "source_overlap": source_overlap,
        "translation_overlap": translation_overlap,
        "source_excerpt_sha256": sha256_text(source_excerpt) if source_excerpt else None,
        "translation_excerpt_sha256": sha256_text(translation_excerpt) if translation_excerpt else None,
        "case_source_offset": source_offset,
        "case_translation_offset": translation_offset,
        "human_confirmed": human_confirmed,
        "ambiguity_reason": ambiguity,
    }


def link_all_evidence(evidence_items: list[dict[str, Any]], cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [link_evidence(item, cases) for item in evidence_items]
