from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence

from .models import (
    ApprovalStatus, CharacterContextItem, ContextMemoryRecord, ContextSelectionResult,
    ContextType, DEFAULT_CHARACTER_TOKEN_BUDGET, DEFAULT_CONTEXT_TOKEN_BUDGET,
    EvidenceType, ExpiryKind, ParticipantStatus, RecordStatus, ResolutionStatus,
    SelectedContextItem,
)
from .normalization import normalize_text
from .store import ContextMemoryStore, EVIDENCE_PRIORITY
from .validation import ContextSceneValidationError, parse_timestamp


def estimate_context_tokens(value: str, prefix: str = "") -> int:
    return max(1, math.ceil(len(prefix + value) / 4))


def _scope_eligible(record: ContextMemoryRecord, chapter_id: str | None, scene_id: str | None, sequence_index: int | None, now: datetime) -> tuple[bool, str | None]:
    if record.chapter_id is not None and record.chapter_id != chapter_id:
        return False, "out_of_scope"
    if record.scene_id is not None and record.scene_id != scene_id:
        return False, "out_of_scope"
    if sequence_index is not None and record.sequence_index > sequence_index:
        return False, "out_of_scope"
    policy = record.expiry_policy
    if policy.kind == ExpiryKind.SCENE_SCOPE and policy.scope_id != scene_id:
        return False, "expired"
    if policy.kind == ExpiryKind.CHAPTER_SCOPE and policy.scope_id != chapter_id:
        return False, "expired"
    if policy.kind == ExpiryKind.TIMESTAMP and now >= parse_timestamp(policy.expires_at or "", "expires_at"):
        return False, "expired"
    return True, None


def _priority(record: ContextMemoryRecord) -> int:
    if record.approval_status == ApprovalStatus.APPROVED:
        return 0
    strongest = max(record.evidence, key=lambda item: EVIDENCE_PRIORITY[item.evidence_type]).evidence_type
    mapping = {EvidenceType.SOURCE_OBSERVATION: 20, EvidenceType.TRANSLATION_OBSERVATION: 60, EvidenceType.RULE_DERIVED: 70, EvidenceType.HISTORICAL_IMPORT: 80, EvidenceType.AI_INFERENCE: 90, EvidenceType.HUMAN_REJECTED: 100, EvidenceType.HUMAN_APPROVED: 0}
    if record.context_type == ContextType.UNRESOLVED_REFERENCE:
        return min(mapping[strongest], 30)
    return mapping[strongest]


def select_context_for_translation(
    context_store: ContextMemoryStore, *, chapter_id: str | None = None,
    scene_id: str | None = None, sequence_index: int | None = None,
    character_ids: Sequence[str] | None = None, source_language: str | None = None,
    token_budget: int = DEFAULT_CONTEXT_TOKEN_BUDGET,
    character_context_view: Sequence[CharacterContextItem] = (),
    character_token_budget: int = DEFAULT_CHARACTER_TOKEN_BUDGET,
    include_previous_translation: bool = True, include_unresolved: bool = True,
    include_experimental_inference: bool = False,
    expected_previous_translation_hash: str | None = None,
    confidence_threshold: float = 0.75, now: str | None = None,
) -> ContextSelectionResult:
    for value, name in ((token_budget, "token_budget"), (character_token_budget, "character_token_budget")):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ContextSceneValidationError(f"{name} must be a non-negative integer")
    current_time = datetime.now(timezone.utc) if now is None else parse_timestamp(now, "selection now")
    dropped: dict[str, list[str]] = {}
    candidates: list[tuple[int, int, str, SelectedContextItem, str]] = []
    conflict_ids = context_store.unresolved_conflict_ids()
    seen_values: set[tuple[str, str]] = set()

    def drop(item_id: str, reason: str) -> None:
        dropped.setdefault(item_id, []).append(reason)

    for record in sorted(context_store.contexts.values(), key=lambda item: item.context_id):
        if record.status not in {RecordStatus.ACTIVE, RecordStatus.PENDING}:
            drop(record.context_id, "expired" if record.status == RecordStatus.EXPIRED else "invalid")
            continue
        if record.context_id in conflict_ids:
            drop(record.context_id, "conflict")
            continue
        eligible, reason = _scope_eligible(record, chapter_id, scene_id, sequence_index, current_time)
        if not eligible:
            drop(record.context_id, reason or "out_of_scope")
            continue
        if source_language is not None and record.source_language != source_language:
            drop(record.context_id, "out_of_scope")
            continue
        if record.confidence < confidence_threshold and record.approval_status != ApprovalStatus.APPROVED:
            drop(record.context_id, "invalid")
            continue
        types = {item.evidence_type for item in record.evidence}
        if EvidenceType.AI_INFERENCE in types and not include_experimental_inference:
            drop(record.context_id, "ineligible_inference")
            continue
        if record.experimental_only and not include_experimental_inference:
            drop(record.context_id, "ineligible_inference")
            continue
        if record.context_type == ContextType.PREVIOUS_TRANSLATION_EXCERPT:
            if not include_previous_translation:
                drop(record.context_id, "lower_priority")
                continue
            hashes = {item.translation_text_hash for item in record.evidence if item.translation_text_hash}
            stale_sequence = sequence_index is not None and record.sequence_index != max(0, sequence_index - 1)
            stale_hash = expected_previous_translation_hash is not None and expected_previous_translation_hash not in hashes
            if stale_sequence or stale_hash:
                drop(record.context_id, "stale")
                continue
        key = (record.context_type.value, normalize_text(record.value).casefold())
        if key in seen_values:
            drop(record.context_id, "duplicate")
            continue
        seen_values.add(key)
        cost = estimate_context_tokens(record.value, record.context_type.value)
        item = SelectedContextItem(record.context_id, record.context_type.value, record.value, tuple(sorted(ev.evidence_id for ev in record.evidence)), cost, _priority(record))
        candidates.append((item.priority, -record.sequence_index, item.item_id, item, "context"))

    if scene_id is not None and scene_id in context_store.scenes:
        scene = context_store.scenes[scene_id]
        allowed_characters = None if character_ids is None else set(character_ids)
        for participant in scene.participants:
            if participant.participant_status not in {ParticipantStatus.PRESENT, ParticipantStatus.MENTIONED} or participant.unresolved_identity:
                continue
            if allowed_characters is not None and participant.character_id not in allowed_characters:
                continue
            value = f"{participant.character_id}:{participant.participant_status.value}"
            item = SelectedContextItem(f"participant:{scene_id}:{participant.character_id}", "scene_participant", value, (participant.evidence_reference,), estimate_context_tokens(value), 25)
            candidates.append((25, 0, item.item_id, item, "participant"))
        if include_unresolved:
            for reference in scene.unresolved_references:
                if reference.resolution_status in {ResolutionStatus.REJECTED, ResolutionStatus.EXPIRED}:
                    continue
                value = reference.surface_form if reference.resolved_target is None else f"{reference.surface_form}->{reference.resolved_target}"
                priority = 5 if reference.resolution_status == ResolutionStatus.HUMAN_APPROVED else 30
                item = SelectedContextItem(reference.reference_id, "unresolved_reference", value, tuple(sorted(ev.evidence_id for ev in reference.evidence)), estimate_context_tokens(value), priority)
                candidates.append((priority, 0, item.item_id, item, "reference"))

    selected = []
    used = 0
    for _, _, _, item, _ in sorted(candidates):
        if used + item.estimated_tokens > token_budget:
            drop(item.item_id, "over_budget")
            continue
        selected.append(item)
        used += item.estimated_tokens

    selected_chars = []
    char_used = 0
    allowed_characters = None if character_ids is None else set(character_ids)
    for item in sorted(character_context_view, key=lambda value: (value.character_id, value.fact_type, value.memory_id)):
        if allowed_characters is not None and item.character_id not in allowed_characters:
            continue
        if char_used + item.estimated_tokens > character_token_budget:
            drop(item.memory_id, "over_budget")
            continue
        selected_chars.append(item)
        char_used += item.estimated_tokens
    fingerprint_body = {"context": [item.item_id for item in selected], "character": [item.memory_id for item in selected_chars], "context_tokens": used, "character_tokens": char_used, "budgets": [token_budget, character_token_budget]}
    fingerprint = hashlib.sha256(json.dumps(fingerprint_body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    all_dropped = tuple(sorted(dropped))
    return ContextSelectionResult(tuple(selected), tuple(selected_chars), used, char_used, token_budget, character_token_budget, all_dropped, {key: tuple(sorted(set(value))) for key, value in sorted(dropped.items())}, fingerprint)
