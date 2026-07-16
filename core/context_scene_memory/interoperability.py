from __future__ import annotations

from core.character_memory_v2 import MemoryStore, select_prompt_eligible_memories

from .models import CharacterContextItem, ParticipantStatus, SceneParticipant
from .validation import ContextSceneValidationError


def build_character_context_view(
    character_store: MemoryStore, *, character_ids: tuple[str, ...] | None = None,
    token_budget: int = 256, now: str | None = None,
) -> tuple[CharacterContextItem, ...]:
    result = select_prompt_eligible_memories(character_store, character_ids=character_ids, token_budget=token_budget, now=now)
    return tuple(CharacterContextItem(item.memory_id, item.character_id, item.fact_type.value, item.value, item.evidence_ids, item.estimated_tokens) for item in result.items)


def link_character_memory(
    character_store: MemoryStore, *, character_id: str, participant_status: ParticipantStatus | str,
    presence_confidence: float, evidence_reference: str,
) -> SceneParticipant:
    records = [item for item in character_store.records.values() if item.character_id == character_id]
    if not records:
        raise ContextSceneValidationError("unknown character reference")
    version = max(item.version for item in records)
    unresolved = all(item.unresolved_identity for item in records)
    return SceneParticipant(character_id, version, participant_status if isinstance(participant_status, ParticipantStatus) else ParticipantStatus(participant_status), float(presence_confidence), evidence_reference, unresolved)


def resolve_scene_participant_reference(character_store: MemoryStore, participant: SceneParticipant) -> tuple[CharacterContextItem, ...]:
    if participant.unresolved_identity:
        return ()
    return build_character_context_view(character_store, character_ids=(participant.character_id,))
