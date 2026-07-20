from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .eligibility import is_prompt_eligible
from .models import NameResolutionRecord
from .normalization import normalize_source_name


SOURCE_PRIORITY = {"human_review": 0, "glossary": 1, "corpus": 2, "character_memory": 3, "none": 9}


def resolve_name(source_name: str, candidates: Iterable[NameResolutionRecord]) -> NameResolutionRecord:
    normalized = normalize_source_name(source_name)
    matches = [item for item in candidates if item.normalized_source_name == normalized]
    approved = [item for item in matches if is_prompt_eligible(item)]
    approved_targets = sorted({item.approved_zh_hant_name for item in approved if item.approved_zh_hant_name})
    if len(approved_targets) > 1:
        evidence = tuple(sorted({evidence for item in approved for evidence in item.evidence_ids}))
        return NameResolutionRecord.create(
            source_name=source_name, mapping_status="conflicting_target_mapping",
            mapping_source="none", evidence_ids=evidence, approval_status="unreviewed",
            unresolved_reason="conflicting_approved_target_mappings", conflict_state=True,
        )
    if approved:
        return sorted(
            approved,
            key=lambda item: (
                SOURCE_PRIORITY[item.mapping_source], item.normalized_source_name,
                item.deterministic_fingerprint,
            ),
        )[0]
    identity = [item for item in matches if item.identity_transliteration]
    if identity:
        chosen = sorted(identity, key=lambda item: (item.normalized_source_name, item.deterministic_fingerprint))[0]
        return NameResolutionRecord.create(
            source_name=chosen.source_name, source_language=chosen.source_language,
            identity_transliteration=chosen.identity_transliteration,
            approved_zh_hant_name=None, mapping_status="identity_only",
            mapping_source=chosen.mapping_source, evidence_ids=chosen.evidence_ids,
            approval_status=chosen.approval_status, unresolved_reason="missing_approved_zh_hant_name",
        )
    evidence = tuple(sorted({evidence for item in matches for evidence in item.evidence_ids}))
    return NameResolutionRecord.create(
        source_name=source_name, mapping_status="missing_approved_target_name",
        mapping_source="none", evidence_ids=evidence, approval_status="unreviewed",
        unresolved_reason="no_authoritative_target_mapping",
    )


def resolve_inventory(
    source_names: Iterable[str], candidates: Iterable[NameResolutionRecord],
) -> tuple[NameResolutionRecord, ...]:
    candidate_tuple = tuple(candidates)
    seen: set[str] = set()
    ordered: list[NameResolutionRecord] = []
    for source_name in source_names:
        normalized = normalize_source_name(source_name)
        if normalized not in seen:
            ordered.append(resolve_name(source_name, candidate_tuple))
            seen.add(normalized)
    return tuple(ordered)
