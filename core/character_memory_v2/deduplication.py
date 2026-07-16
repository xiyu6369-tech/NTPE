from __future__ import annotations

from typing import Iterable

from .models import Evidence, EvidenceType, MemoryRecord
from .normalization import canonical_conflict_key, canonical_fact_key, canonical_hash


EVIDENCE_PRIORITY = {
    EvidenceType.HUMAN_REJECTED: 0,
    EvidenceType.AI_INFERENCE: 10,
    EvidenceType.HISTORICAL_IMPORT: 20,
    EvidenceType.TRANSLATION_OBSERVATION: 30,
    EvidenceType.SOURCE_OBSERVATION: 40,
    EvidenceType.HUMAN_APPROVED: 50,
}


def fact_key(record: MemoryRecord) -> tuple[str, str, str]:
    return canonical_fact_key(record.character_id, record.fact_type.value, record.value)


def conflict_key(record: MemoryRecord) -> tuple[str, str]:
    return canonical_conflict_key(record.character_id, record.fact_type.value)


def evidence_rank(record: MemoryRecord) -> int:
    return max(EVIDENCE_PRIORITY[item.evidence_type] for item in record.evidence)


def merge_evidence(*groups: Iterable[Evidence]) -> tuple[Evidence, ...]:
    by_id: dict[str, Evidence] = {}
    for group in groups:
        for item in group:
            by_id[item.evidence_id] = item
    return tuple(sorted(by_id.values(), key=lambda item: item.evidence_id))


def strongest_evidence_type(evidence: Iterable[Evidence]) -> EvidenceType:
    return max((item.evidence_type for item in evidence), key=lambda item: (EVIDENCE_PRIORITY[item], item.value))


def conflict_id(character_id: str, fact_type: str, memory_ids: Iterable[str]) -> str:
    return "conf_" + canonical_hash((character_id, fact_type, *sorted(set(memory_ids))))[:24]

