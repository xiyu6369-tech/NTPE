from __future__ import annotations

from dataclasses import replace

from .models import ContextMemoryRecord, RecordStatus
from .store import ContextMemoryStore, _merge_evidence, utc_now
from .validation import ContextSceneValidationError, parse_timestamp, validate_context_record


def expire_context(store: ContextMemoryStore, context_id: str, *, expired_at: str | None = None) -> ContextMemoryRecord:
    current = store.get_context(context_id)
    if current.status not in {RecordStatus.ACTIVE, RecordStatus.PENDING}:
        raise ContextSceneValidationError("only active context can expire")
    timestamp = expired_at or utc_now()
    parse_timestamp(timestamp, "expired_at")
    updated = replace(current, status=RecordStatus.EXPIRED, updated_at=timestamp, version=current.version + 1)
    store._update_context(updated)
    return updated


def reject_context(store: ContextMemoryStore, context_id: str, *, rejected_at: str | None = None) -> ContextMemoryRecord:
    current = store.get_context(context_id)
    if current.status not in {RecordStatus.ACTIVE, RecordStatus.PENDING}:
        raise ContextSceneValidationError("context cannot be rejected in current status")
    timestamp = rejected_at or utc_now()
    updated = replace(current, status=RecordStatus.REJECTED, updated_at=timestamp, version=current.version + 1)
    store._update_context(updated)
    return updated


def supersede_context(store: ContextMemoryStore, context_id: str, *, replacement_id: str, updated_at: str | None = None) -> ContextMemoryRecord:
    current = store.get_context(context_id)
    replacement = store.get_context(replacement_id)
    if current.context_type != replacement.context_type or current.chapter_id != replacement.chapter_id or current.scene_id != replacement.scene_id:
        raise ContextSceneValidationError("supersede requires matching context scope and type")
    timestamp = updated_at or utc_now()
    updated = replace(current, status=RecordStatus.SUPERSEDED, updated_at=timestamp, version=current.version + 1)
    store._update_context(updated)
    return updated


def rollback_context(store: ContextMemoryStore, context_id: str, *, target_version: int | None = None, rolled_back_at: str | None = None) -> ContextMemoryRecord:
    current = store.get_context(context_id)
    history = list(store.context_history.get(context_id, []))
    candidates = history if target_version is None else [item for item in history if item.version == target_version]
    if not candidates:
        raise ContextSceneValidationError("invalid rollback target")
    target = candidates[-1]
    timestamp = rolled_back_at or utc_now()
    restored = replace(target, evidence=_merge_evidence(target.evidence, current.evidence), updated_at=timestamp, version=current.version + 1)
    validate_context_record(restored)
    store._update_context(restored)
    return restored


def rollback_scene(store: ContextMemoryStore, scene_id: str, *, target_version: int | None = None, rolled_back_at: str | None = None):
    current = store.get_scene(scene_id)
    history = list(store.scene_history.get(scene_id, []))
    candidates = history if target_version is None else [item for item in history if item.scene_version == target_version]
    if not candidates:
        raise ContextSceneValidationError("invalid scene rollback target")
    target = candidates[-1]
    timestamp = rolled_back_at or utc_now()
    restored = replace(target, evidence=_merge_evidence(target.evidence, current.evidence), updated_at=timestamp, scene_version=current.scene_version + 1)
    store._update_scene(restored)
    return restored
