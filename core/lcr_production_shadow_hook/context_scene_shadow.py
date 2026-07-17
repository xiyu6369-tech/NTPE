from __future__ import annotations

import hashlib
import json
import time
from dataclasses import replace
from types import MappingProxyType
from typing import Mapping, Sequence

from core.context_scene_memory import (
    ContextMemoryStore, ContextType, ParticipantStatus, RecordStatus, ResolutionStatus,
    select_context_for_translation, validate_context_store,
)

from .models import ContextSceneShadowInput, ContextSceneShadowResult


DEFAULT_CONTEXT_SCENE_SHADOW_BUDGET = 256
MAX_COMBINED_HYPOTHETICAL_BUDGET = 384
PROFILE_IDENTITIES = {
    "ko": ("literary-ko-zh-hant", "1.0"),
    "ja": ("literary-ja-zh-hant", "1.0"),
    "en": ("literary-en-zh-hant", "1.0"),
}


def _hash(value: object) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _invalid_identifier(value: str) -> bool:
    return not value or "/" in value or "\\" in value or value in {".", ".."}


def _redacted_record(record: object) -> object:
    evidence = tuple(replace(item, excerpt="[redacted]") for item in record.evidence)
    if record.context_type == ContextType.PREVIOUS_TRANSLATION_EXCERPT:
        value = f"[previous-translation-redacted:{_hash(record.value)[:16]}:chars={len(record.value)}]"
    else:
        value = record.value[:96] + ("…" if len(record.value) > 96 else "")
    return replace(record, value=value, evidence=evidence)


def _redacted_scene(scene: object) -> object:
    evidence = tuple(replace(item, excerpt="[redacted]") for item in scene.evidence)
    participants = tuple(replace(item, evidence_reference=_hash(item.evidence_reference)[:16]) for item in scene.participants)
    references = tuple(
        replace(item, surface_form="[redacted-reference]",
                evidence=tuple(replace(ev, excerpt="[redacted]") for ev in item.evidence))
        for item in scene.unresolved_references
    )
    return replace(scene, location="[present]" if scene.location else None,
                   time_state="[present]" if scene.time_state else None,
                   event_state=tuple(_hash(item)[:16] for item in scene.event_state),
                   participants=participants, unresolved_references=references, evidence=evidence)


def build_context_scene_shadow_input(
    store: ContextMemoryStore,
    *,
    document_id: str,
    chunk_index: int,
    source_language: str,
    target_language: str,
    chapter_id: str,
    scene_id: str,
    sequence_index: int,
    character_ids: Sequence[str] = (),
    snapshot_id: str,
    scope: Mapping[str, str] | None = None,
    token_budget: int = DEFAULT_CONTEXT_SCENE_SHADOW_BUDGET,
    previous_translation_allowed: bool = False,
    expected_previous_translation_hash: str = "",
    character_memory_selection_fingerprint: str = "",
    created_at: str = "",
) -> ContextSceneShadowInput:
    """Build a detached, redacted immutable view on the caller thread."""
    if not isinstance(store, ContextMemoryStore):
        raise ValueError("context_store must be ContextMemoryStore")
    identifiers = (document_id, chapter_id, scene_id, snapshot_id, *character_ids)
    if any(_invalid_identifier(str(item)) for item in identifiers):
        raise ValueError("context identifiers cannot contain path traversal or separators")
    for value, name in ((chunk_index, "chunk_index"), (sequence_index, "sequence_index"), (token_budget, "token_budget")):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if not validate_context_store(store)["valid"]:
        raise ValueError("invalid context store")
    profile = PROFILE_IDENTITIES.get(str(source_language).lower())
    if profile is None or target_language != "zh-Hant":
        raise ValueError("unsupported multilingual profile")
    payload = json.loads(json.dumps(store.to_dict(), ensure_ascii=False))
    copied = ContextMemoryStore.from_dict(payload)
    records = tuple(_redacted_record(copied.contexts[key]) for key in sorted(copied.contexts))
    scenes = tuple(_redacted_scene(copied.scenes[key]) for key in sorted(copied.scenes))
    conflicts = tuple((key, tuple(copied.conflicts[key])) for key in sorted(copied.conflicts))
    return ContextSceneShadowInput(
        document_id=str(document_id), chunk_index=chunk_index,
        source_language=str(source_language).lower(), target_language=str(target_language),
        chapter_id=str(chapter_id), scene_id=str(scene_id), sequence_index=sequence_index,
        character_ids=tuple(sorted(set(str(item) for item in character_ids))),
        snapshot_id=str(snapshot_id), schema_version=str(copied.schema_version),
        store_fingerprint=_hash(payload),
        scope=MappingProxyType({str(k): str(v) for k, v in sorted((scope or {}).items())}),
        token_budget=token_budget, previous_translation_allowed=bool(previous_translation_allowed),
        expected_previous_translation_hash=str(expected_previous_translation_hash),
        profile_id=profile[0], profile_version=profile[1],
        character_memory_selection_fingerprint=str(character_memory_selection_fingerprint),
        created_at=str(created_at), records=records, scenes=scenes, conflicts=conflicts,
    )


def _working_store(snapshot: ContextSceneShadowInput) -> ContextMemoryStore:
    store = ContextMemoryStore()
    store.contexts = {item.context_id: item for item in snapshot.records}
    store.scenes = {item.scene_id: item for item in snapshot.scenes}
    store.context_history = {item.context_id: [] for item in snapshot.records}
    store.scene_history = {item.scene_id: [] for item in snapshot.scenes}
    store.conflicts = dict(snapshot.conflicts)
    store.snapshot_version = len(snapshot.records) + len(snapshot.scenes) + len(snapshot.conflicts)
    return store


def empty_context_scene_result(*, status: str, snapshot_id: str = "", store_fingerprint: str = "",
                               token_budget: int = DEFAULT_CONTEXT_SCENE_SHADOW_BUDGET) -> ContextSceneShadowResult:
    empty = _hash([])
    return ContextSceneShadowResult(
        module="context_scene", status=status, snapshot_id=snapshot_id, store_fingerprint=store_fingerprint,
        chapter_id="", scene_id="", scene_version=0, participant_counts=MappingProxyType({}),
        present_character_ids=(), mentioned_character_ids=(), exited_character_ids=(),
        active_speaker_status="unavailable", point_of_view_status="unavailable",
        location_state_present=False, time_state_present=False, unresolved_reference_count=0,
        unresolved_reference_evidence=(), selected_context_ids=(), selected_context_types=(),
        selected_fingerprint=empty, combined_context_fingerprint=empty, estimated_tokens=0,
        budget=token_budget, available_records=0, eligible_records=0, selected_records=0,
        dropped_records=0, drop_reasons=MappingProxyType({}), duplicate_savings=0,
        stale_excluded=0, expired_excluded=0, conflict_excluded=0, inference_excluded=0,
        previous_translation_candidate=False, previous_translation_selected=False,
    )


def evaluate_context_scene_shadow(snapshot: ContextSceneShadowInput, *, now: str | None = None) -> ContextSceneShadowResult:
    """Use only the Batch 3 validator/selector and return non-content evidence."""
    started = time.perf_counter_ns()
    try:
        store = _working_store(snapshot)
        if not validate_context_store(store)["valid"]:
            return empty_context_scene_result(status="invalid", snapshot_id=snapshot.snapshot_id,
                                              store_fingerprint=snapshot.store_fingerprint,
                                              token_budget=snapshot.token_budget)
        selection = select_context_for_translation(
            store, chapter_id=snapshot.chapter_id, scene_id=snapshot.scene_id,
            sequence_index=snapshot.sequence_index, character_ids=snapshot.character_ids,
            source_language=snapshot.source_language, token_budget=snapshot.token_budget,
            character_token_budget=0, include_previous_translation=snapshot.previous_translation_allowed,
            include_unresolved=True, include_experimental_inference=False,
            expected_previous_translation_hash=snapshot.expected_previous_translation_hash or None,
            now=now or snapshot.created_at or None,
        )
    except Exception:
        return empty_context_scene_result(status="invalid", snapshot_id=snapshot.snapshot_id,
                                          store_fingerprint=snapshot.store_fingerprint,
                                          token_budget=snapshot.token_budget)
    reasons: dict[str, int] = {}
    for values in selection.drop_reasons.values():
        for reason in values:
            reasons[reason] = reasons.get(reason, 0) + 1
    selected_ids = tuple(item.item_id for item in selection.selected_records)
    selected_types = tuple(item.item_type for item in selection.selected_records)
    previous_records = tuple(item for item in snapshot.records if item.context_type == ContextType.PREVIOUS_TRANSLATION_EXCERPT)
    previous_candidate = snapshot.previous_translation_allowed and bool(previous_records) and reasons.get("stale", 0) < len(previous_records)
    previous_selected = ContextType.PREVIOUS_TRANSLATION_EXCERPT.value in selected_types
    scene = next((item for item in snapshot.scenes if item.scene_id == snapshot.scene_id and item.chapter_id == snapshot.chapter_id
                  and item.status in {RecordStatus.ACTIVE, RecordStatus.PENDING}), None)
    participants = () if scene is None else scene.participants
    counts = {status.value: sum(1 for item in participants if item.participant_status == status) for status in ParticipantStatus}
    counts = {key: value for key, value in counts.items() if value}
    references = () if scene is None else scene.unresolved_references
    reference_evidence = tuple(MappingProxyType({
        "reference_id": item.reference_id, "resolution_status": item.resolution_status.value,
        "candidate_count": len(item.candidate_targets),
        "evidence_type": ",".join(sorted({ev.evidence_type.value for ev in item.evidence})),
        "scope": item.scope,
    }) for item in references if item.resolution_status not in {ResolutionStatus.REJECTED, ResolutionStatus.EXPIRED})
    combined = _hash({"character": snapshot.character_memory_selection_fingerprint,
                      "context": selection.deterministic_fingerprint,
                      "profile": [snapshot.profile_id, snapshot.profile_version]})
    if selection.selected_records:
        status = "budget_limited" if reasons.get("over_budget") else "selected"
    elif reasons.get("conflict"):
        status = "conflict_excluded"
    elif reasons.get("stale"):
        status = "stale_context_excluded"
    elif reasons.get("out_of_scope"):
        status = "scope_mismatch"
    else:
        status = "no_eligible_context"
    if reference_evidence and status == "no_eligible_context":
        status = "unresolved_preserved"
    duration = (time.perf_counter_ns() - started) / 1_000_000
    return ContextSceneShadowResult(
        module="context_scene", status=status, snapshot_id=snapshot.snapshot_id,
        store_fingerprint=snapshot.store_fingerprint, chapter_id=snapshot.chapter_id,
        scene_id=snapshot.scene_id, scene_version=0 if scene is None else scene.scene_version,
        participant_counts=MappingProxyType(dict(sorted(counts.items()))),
        present_character_ids=tuple(sorted(item.character_id for item in participants if item.participant_status == ParticipantStatus.PRESENT and not item.unresolved_identity)),
        mentioned_character_ids=tuple(sorted(item.character_id for item in participants if item.participant_status == ParticipantStatus.MENTIONED and not item.unresolved_identity)),
        exited_character_ids=tuple(sorted(item.character_id for item in participants if item.participant_status == ParticipantStatus.EXITED_SCENE)),
        active_speaker_status="unavailable" if scene is None or not scene.active_speaker else
            ("present" if scene.active_speaker in {item.character_id for item in participants if item.participant_status == ParticipantStatus.PRESENT} else "not_present"),
        point_of_view_status="present" if scene is not None and scene.point_of_view else "unavailable",
        location_state_present=bool(scene is not None and scene.location),
        time_state_present=bool(scene is not None and scene.time_state),
        unresolved_reference_count=len(reference_evidence), unresolved_reference_evidence=reference_evidence,
        selected_context_ids=selected_ids, selected_context_types=selected_types,
        selected_fingerprint=selection.deterministic_fingerprint, combined_context_fingerprint=combined,
        estimated_tokens=selection.estimated_tokens, budget=selection.budget,
        available_records=len(snapshot.records),
        eligible_records=len(selection.selected_records) + reasons.get("over_budget", 0),
        selected_records=len(selection.selected_records), dropped_records=len(selection.dropped_records),
        drop_reasons=MappingProxyType(dict(sorted(reasons.items()))), duplicate_savings=reasons.get("duplicate", 0),
        stale_excluded=reasons.get("stale", 0), expired_excluded=reasons.get("expired", 0),
        conflict_excluded=reasons.get("conflict", 0), inference_excluded=reasons.get("ineligible_inference", 0),
        previous_translation_candidate=previous_candidate, previous_translation_selected=previous_selected,
        cache_identity_impact_planned=bool(selection.selected_records), duration_ms=round(duration, 6),
    )
