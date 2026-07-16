from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .deduplication import EVIDENCE_PRIORITY, fact_key
from .models import (
    ApprovalStatus,
    DEFAULT_PROMPT_TOKEN_BUDGET,
    EvidenceType,
    ExpiryKind,
    FactType,
    MemoryRecord,
    MemoryStatus,
    PromptMemoryItem,
    SelectionResult,
)
from .store import MemoryStore
from .validation import CharacterMemoryValidationError, parse_timestamp


_STABILITY = {
    FactType.CANONICAL_NAME: 0,
    FactType.NAME_VARIANT: 1,
    FactType.ROLE_OR_IDENTITY: 2,
    FactType.RELATIONSHIP: 3,
    FactType.TERMINOLOGY_PREFERENCE: 4,
    FactType.ADDRESSING_STYLE: 5,
    FactType.SPEECH_STYLE: 6,
    FactType.PRONOUN_OR_GENDER_REFERENCE: 7,
    FactType.PERSONALITY_TRAIT: 8,
    FactType.APPEARANCE: 9,
    FactType.OTHER: 10,
    FactType.TEMPORAL_STATE: 20,
    FactType.LOCATION_STATE: 21,
}


def estimate_memory_tokens(record: MemoryRecord) -> int:
    structured = f"{record.character_id}|{record.fact_type.value}|{record.value}"
    return max(1, math.ceil(len(structured) / 4))


def _scope_eligible(record: MemoryRecord, scope: Mapping[str, str], now: datetime) -> bool:
    policy = record.expiry_policy
    if policy.kind == ExpiryKind.NEVER:
        return True
    if policy.kind == ExpiryKind.MANUAL_REVIEW_REQUIRED:
        return record.approval_status == ApprovalStatus.APPROVED
    if policy.kind == ExpiryKind.TIMESTAMP:
        assert policy.expires_at is not None
        return now < parse_timestamp(policy.expires_at, "expires_at")
    key = {
        ExpiryKind.SEGMENT_SCOPE: "segment_id",
        ExpiryKind.CHAPTER_SCOPE: "chapter_id",
        ExpiryKind.SESSION_SCOPE: "session_id",
    }[policy.kind]
    return bool(policy.scope_id and scope.get(key) == policy.scope_id)


def _language_eligible(record: MemoryRecord, language_profile: Mapping[str, Any] | str | None) -> bool:
    if language_profile is None:
        return True
    if isinstance(language_profile, str):
        return record.source_language == language_profile
    languages = language_profile.get("source_languages")
    return True if languages is None else record.source_language in set(str(item) for item in languages)


def _priority(record: MemoryRecord) -> tuple[int, int, float, str]:
    approved = 0 if record.approval_status == ApprovalStatus.APPROVED else 1
    evidence = max(EVIDENCE_PRIORITY[item.evidence_type] for item in record.evidence)
    recency = -parse_timestamp(record.updated_at, "updated_at").timestamp()
    return approved, -evidence, _STABILITY[record.fact_type] + recency / 10**12, record.memory_id


def _selection_integrity_valid(memory_id: str, record: MemoryRecord) -> bool:
    """Cheap fail-closed guard for records already validated on store mutation."""
    return bool(
        memory_id == record.memory_id
        and record.character_id
        and record.value
        and record.evidence
        and 0.0 <= record.confidence <= 1.0
        and record.version >= 1
        and record.source_case_id
        and record.source_segment_id
        and record.evidence_type in {item.evidence_type for item in record.evidence}
    )


def select_prompt_eligible_memories(
    store: MemoryStore,
    *,
    character_ids: Sequence[str] | None = None,
    token_budget: int = DEFAULT_PROMPT_TOKEN_BUDGET,
    language_profile: Mapping[str, Any] | str | None = None,
    include_pending: bool = False,
    confidence_threshold: float = 0.85,
    scope: Mapping[str, str] | None = None,
    now: str | None = None,
) -> SelectionResult:
    if not isinstance(token_budget, int) or isinstance(token_budget, bool) or token_budget < 0:
        raise CharacterMemoryValidationError("token_budget must be a non-negative integer")
    if not 0.0 <= confidence_threshold <= 1.0:
        raise CharacterMemoryValidationError("confidence_threshold must be between 0.0 and 1.0")
    if token_budget == 0:
        return SelectionResult(token_budget=0, estimated_tokens=0, excluded_counts={"budget": len(store.records)})
    selected_characters = None if character_ids is None else set(character_ids)
    current_scope = dict(scope or {})
    current_time = datetime.now(timezone.utc) if now is None else parse_timestamp(now, "selection now")
    unresolved = store.unresolved_memory_ids()
    excluded: dict[str, int] = {}
    eligible: list[MemoryRecord] = []
    seen_facts: set[tuple[str, str, str]] = set()

    def exclude(reason: str) -> None:
        excluded[reason] = excluded.get(reason, 0) + 1

    for memory_id, record in sorted(store.records.items()):
        if not _selection_integrity_valid(memory_id, record):
            exclude("invalid")
            continue
        if record.status != MemoryStatus.ACTIVE:
            exclude(record.status.value)
            continue
        if record.memory_id in unresolved:
            exclude("unresolved_conflict")
            continue
        if record.unresolved_identity:
            exclude("unresolved_identity")
            continue
        if selected_characters is not None and record.character_id not in selected_characters:
            exclude("character_scope")
            continue
        if not _language_eligible(record, language_profile):
            exclude("language_profile")
            continue
        if not _scope_eligible(record, current_scope, current_time):
            exclude("expiry_or_scope")
            continue
        if record.confidence < confidence_threshold and record.approval_status != ApprovalStatus.APPROVED:
            exclude("confidence")
            continue
        if record.evidence_type == EvidenceType.AI_INFERENCE and not include_pending:
            exclude("ai_inference")
            continue
        if record.approval_status == ApprovalStatus.PENDING and not include_pending and record.evidence_type not in {EvidenceType.SOURCE_OBSERVATION, EvidenceType.TRANSLATION_OBSERVATION}:
            exclude("pending")
            continue
        key = fact_key(record)
        if key in seen_facts:
            exclude("duplicate")
            continue
        seen_facts.add(key)
        eligible.append(record)

    items: list[PromptMemoryItem] = []
    used = 0
    for record in sorted(eligible, key=_priority):
        cost = estimate_memory_tokens(record)
        if used + cost > token_budget:
            exclude("budget")
            continue
        priority = _priority(record)[0] * 100 + _STABILITY[record.fact_type]
        items.append(PromptMemoryItem(
            memory_id=record.memory_id,
            character_id=record.character_id,
            fact_type=record.fact_type,
            value=record.value,
            evidence_ids=tuple(sorted(item.evidence_id for item in record.evidence)),
            estimated_tokens=cost,
            priority=priority,
        ))
        used += cost
    return SelectionResult(tuple(items), token_budget, used, dict(sorted(excluded.items())))
