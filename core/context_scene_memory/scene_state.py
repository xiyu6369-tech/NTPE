from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .lifecycle import expire_context
from .models import (
    BoundaryType, ContextEvidence, EvidenceType, ExpiryKind, ParticipantStatus, RecordStatus,
    ResolutionStatus, SceneParticipant, UnresolvedReference,
)
from .store import ContextMemoryStore, _merge_evidence, create_scene_memory, utc_now
from .validation import ContextSceneValidationError, parse_timestamp


_UNSET = object()


def update_scene_state(
    store: ContextMemoryStore, scene_id: str, *, location: str | None | object = _UNSET,
    time_state: str | None | object = _UNSET, active_speaker: str | None | object = _UNSET,
    point_of_view: str | None | object = _UNSET, event_state: Iterable[str] | object = _UNSET,
    evidence: ContextEvidence | None = None, updated_at: str | None = None,
):
    current = store.get_scene(scene_id)
    timestamp = updated_at or utc_now()
    parse_timestamp(timestamp, "updated_at")
    updated = replace(
        current,
        location=current.location if location is _UNSET else location,
        time_state=current.time_state if time_state is _UNSET else time_state,
        active_speaker=current.active_speaker if active_speaker is _UNSET else active_speaker,
        point_of_view=current.point_of_view if point_of_view is _UNSET else point_of_view,
        event_state=current.event_state if event_state is _UNSET else tuple(event_state),
        evidence=current.evidence if evidence is None else _merge_evidence(current.evidence, (evidence,)),
        updated_at=timestamp,
        scene_version=current.scene_version + 1,
    )
    store._update_scene(updated)
    return updated


def add_scene_participant(
    store: ContextMemoryStore, scene_id: str, *, character_id: str,
    participant_status: ParticipantStatus | str, presence_confidence: float,
    evidence_reference: str, memory_version: int | None = None,
    unresolved_identity: bool = False, updated_at: str | None = None,
):
    current = store.get_scene(scene_id)
    status = participant_status if isinstance(participant_status, ParticipantStatus) else ParticipantStatus(participant_status)
    participant = SceneParticipant(character_id, memory_version, status, float(presence_confidence), evidence_reference, unresolved_identity)
    by_id = {item.character_id: item for item in current.participants}
    by_id[character_id] = participant
    timestamp = updated_at or utc_now()
    updated = replace(current, participants=tuple(by_id[key] for key in sorted(by_id)), updated_at=timestamp, scene_version=current.scene_version + 1)
    store._update_scene(updated)
    return updated


def remove_scene_participant(store: ContextMemoryStore, scene_id: str, *, character_id: str, updated_at: str | None = None):
    current = store.get_scene(scene_id)
    by_id = {item.character_id: item for item in current.participants}
    if character_id not in by_id:
        raise ContextSceneValidationError("unknown scene participant")
    by_id[character_id] = replace(by_id[character_id], participant_status=ParticipantStatus.EXITED_SCENE)
    timestamp = updated_at or utc_now()
    updated = replace(current, participants=tuple(by_id[key] for key in sorted(by_id)), active_speaker=None if current.active_speaker == character_id else current.active_speaker, updated_at=timestamp, scene_version=current.scene_version + 1)
    store._update_scene(updated)
    return updated


def add_unresolved_reference(store: ContextMemoryStore, scene_id: str, reference: UnresolvedReference, *, updated_at: str | None = None):
    current = store.get_scene(scene_id)
    by_id = {item.reference_id: item for item in current.unresolved_references}
    if reference.reference_id in by_id:
        raise ContextSceneValidationError("duplicate unresolved reference")
    by_id[reference.reference_id] = reference
    timestamp = updated_at or utc_now()
    updated = replace(current, unresolved_references=tuple(by_id[key] for key in sorted(by_id)), updated_at=timestamp, scene_version=current.scene_version + 1)
    store._update_scene(updated)
    return updated


def resolve_reference(
    store: ContextMemoryStore, scene_id: str, *, reference_id: str, target: str,
    human_approved: bool = False, approval_evidence: ContextEvidence | None = None,
    updated_at: str | None = None,
):
    current = store.get_scene(scene_id)
    by_id = {item.reference_id: item for item in current.unresolved_references}
    if reference_id not in by_id:
        raise ContextSceneValidationError("unknown reference_id")
    reference = by_id[reference_id]
    if len(reference.candidate_targets) > 1 and not human_approved:
        raise ContextSceneValidationError("multiple candidates require human approval")
    if human_approved and approval_evidence is None:
        raise ContextSceneValidationError("human-approved resolution requires evidence")
    if human_approved and approval_evidence is not None and approval_evidence.evidence_type != EvidenceType.HUMAN_APPROVED:
        raise ContextSceneValidationError("approval evidence must be human-approved evidence")
    if not human_approved and target not in reference.candidate_targets:
        raise ContextSceneValidationError("resolved target must be an explicit candidate")
    evidence = reference.evidence if approval_evidence is None else _merge_evidence(reference.evidence, (approval_evidence,))
    status = ResolutionStatus.HUMAN_APPROVED if human_approved else ResolutionStatus.RESOLVED
    by_id[reference_id] = replace(reference, resolved_target=target, resolution_status=status, evidence=evidence)
    timestamp = updated_at or utc_now()
    updated = replace(current, unresolved_references=tuple(by_id[key] for key in sorted(by_id)), updated_at=timestamp, scene_version=current.scene_version + 1)
    store._update_scene(updated)
    return updated


def transition_scene(
    store: ContextMemoryStore, *, from_scene_id: str, boundary: BoundaryType | str,
    to_scene_id: str | None = None, to_chapter_id: str | None = None,
    evidence: ContextEvidence | None = None, transitioned_at: str | None = None,
) -> dict[str, object]:
    kind = boundary if isinstance(boundary, BoundaryType) else BoundaryType(boundary)
    current = store.get_scene(from_scene_id)
    timestamp = transitioned_at or utc_now()
    if kind == BoundaryType.SAME_SCENE:
        return {"boundary": kind.value, "changed": False, "expired_context_ids": [], "target_scene_id": from_scene_id}
    if kind == BoundaryType.UNKNOWN_TRANSITION:
        return {"boundary": kind.value, "changed": False, "conservative": True, "expired_context_ids": [], "target_scene_id": None}
    if not to_scene_id:
        raise ContextSceneValidationError("scene/chapter transition requires target scene_id")
    chapter_transition = kind == BoundaryType.CHAPTER_TRANSITION
    target_chapter = to_chapter_id or current.chapter_id
    if chapter_transition and not to_chapter_id:
        raise ContextSceneValidationError("chapter transition requires target chapter_id")
    expired = []
    for record in list(store.contexts.values()):
        should_expire = record.status == RecordStatus.ACTIVE and (
            (record.expiry_policy.kind == ExpiryKind.SCENE_SCOPE and record.expiry_policy.scope_id == from_scene_id)
            or (chapter_transition and record.expiry_policy.kind == ExpiryKind.CHAPTER_SCOPE and record.expiry_policy.scope_id == current.chapter_id)
        )
        if should_expire:
            expire_context(store, record.context_id, expired_at=timestamp)
            expired.append(record.context_id)
    participants = tuple(replace(item, participant_status=ParticipantStatus.EXITED_SCENE) if item.participant_status == ParticipantStatus.PRESENT else item for item in current.participants)
    references = tuple(replace(item, resolution_status=ResolutionStatus.EXPIRED) if item.resolution_status in {ResolutionStatus.UNRESOLVED, ResolutionStatus.CANDIDATE} else item for item in current.unresolved_references)
    old = replace(current, participants=participants, active_speaker=None, location=None, time_state=None, event_state=(), unresolved_references=references, status=RecordStatus.SUPERSEDED, updated_at=timestamp, scene_version=current.scene_version + 1)
    store._update_scene(old)
    if to_scene_id not in store.scenes:
        new_evidence = evidence or current.evidence[0]
        store._insert_scene(create_scene_memory(scene_id=to_scene_id, chapter_id=target_chapter, evidence=new_evidence, created_at=timestamp))
    return {"boundary": kind.value, "changed": True, "expired_context_ids": sorted(expired), "target_scene_id": to_scene_id}


def transition_chapter(store: ContextMemoryStore, *, from_scene_id: str, to_scene_id: str, to_chapter_id: str, evidence: ContextEvidence, transitioned_at: str | None = None) -> dict[str, object]:
    return transition_scene(store, from_scene_id=from_scene_id, boundary=BoundaryType.CHAPTER_TRANSITION, to_scene_id=to_scene_id, to_chapter_id=to_chapter_id, evidence=evidence, transitioned_at=transitioned_at)
