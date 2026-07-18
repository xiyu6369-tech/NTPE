from __future__ import annotations

from typing import Iterable

from core.character_memory_v2 import FactType, select_prompt_eligible_memories
from core.context_scene_memory import select_context_for_translation

from .models import QualityIntegrationRequest, SelectedQualityContext


_NAME_FACTS = {FactType.CANONICAL_NAME, FactType.NAME_VARIANT}
_SCENE_TYPES = {"scene_participant", "unresolved_reference", "location_state", "temporal_state", "speaker_state", "point_of_view", "event_state"}


def _mentioned_character_ids(source_text: str, store: object, active: Iterable[str]) -> tuple[str, ...]:
    source = source_text.casefold()
    mentioned = {str(item) for item in active if str(item)}
    records = getattr(store, "records", {})
    for memory_id in sorted(records):
        record = records[memory_id]
        character_id = str(record.character_id)
        if character_id and character_id.casefold() in source:
            mentioned.add(character_id)
        elif record.fact_type in _NAME_FACTS and str(record.value).casefold() in source:
            mentioned.add(character_id)
    return tuple(sorted(mentioned))


def _trim(items: Iterable[object], budget: int) -> tuple[object, ...]:
    selected = []
    used = 0
    for item in items:
        cost = int(getattr(item, "estimated_tokens"))
        if used + cost <= budget:
            selected.append(item)
            used += cost
    return tuple(selected)


def select_quality_context(request: QualityIntegrationRequest, *, character_budget: int, context_budget: int, scene_budget: int) -> SelectedQualityContext:
    character_items: tuple[object, ...] = ()
    character_considered = 0
    character_excluded: dict[str, int] = {}
    relevant_ids = tuple(sorted(str(item) for item in request.active_character_ids if str(item)))
    if request.flags.character_enabled and request.character_store is not None:
        character_considered = len(getattr(request.character_store, "records", {}))
        relevant_ids = _mentioned_character_ids(request.source_text, request.character_store, relevant_ids)
        raw = select_prompt_eligible_memories(
            request.character_store,
            character_ids=relevant_ids,
            token_budget=2**31 - 1,
            language_profile=request.source_language,
            include_pending=False,
            scope=request.scope,
            now=request.selection_time,
        )
        active = set(str(item) for item in request.active_character_ids)
        source = request.source_text.casefold()
        ordered = sorted(
            raw.items,
            key=lambda item: (
                0 if (item.character_id.casefold() in source or item.value.casefold() in source) else 1,
                0 if item.character_id in active else 1,
                item.priority,
                item.character_id,
                item.fact_type.value,
                item.memory_id,
            ),
        )
        character_items = _trim(ordered, character_budget)
        character_excluded = dict(raw.excluded_counts)

    context_items: tuple[object, ...] = ()
    scene_items: tuple[object, ...] = ()
    context_considered = 0
    context_dropped: dict[str, tuple[str, ...]] = {}
    if request.flags.context_scene_enabled and request.context_scene_store is not None:
        context_considered = len(getattr(request.context_scene_store, "contexts", {}))
        raw_context = select_context_for_translation(
            request.context_scene_store,
            chapter_id=request.chapter_id,
            scene_id=request.scene_id,
            sequence_index=request.sequence_index,
            character_ids=relevant_ids,
            source_language=request.source_language,
            token_budget=context_budget + scene_budget,
            character_context_view=(),
            character_token_budget=0,
            include_previous_translation=True,
            include_unresolved=True,
            include_experimental_inference=False,
            now=request.selection_time,
        )
        scene_candidates = [item for item in raw_context.selected_records if item.item_type in _SCENE_TYPES]
        context_candidates = [item for item in raw_context.selected_records if item.item_type not in _SCENE_TYPES]
        scene_items = _trim(scene_candidates, scene_budget)
        context_items = _trim(context_candidates, context_budget)
        context_dropped = dict(raw_context.drop_reasons)

    return SelectedQualityContext(
        character_items=character_items,
        context_items=context_items,
        scene_items=scene_items,
        character_considered=character_considered,
        context_considered=context_considered,
        character_excluded=character_excluded,
        context_dropped=context_dropped,
    )

