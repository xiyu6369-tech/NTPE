from __future__ import annotations

from dataclasses import replace

from .deduplication import merge_evidence
from .models import (
    ApprovalMetadata,
    ApprovalStatus,
    ConflictRecord,
    EvidenceType,
    MemoryRecord,
    MemoryStatus,
)
from .store import MemoryStore, create_evidence, utc_now
from .validation import CharacterMemoryValidationError, parse_timestamp, validate_record


def _resolve_conflicts(store: MemoryStore, preferred_memory_id: str, other_memory_id: str, resolution: str) -> None:
    for conflict_id, conflict in list(store.conflicts.items()):
        if {preferred_memory_id, other_memory_id} <= set(conflict.memory_ids):
            store.conflicts[conflict_id] = ConflictRecord(
                conflict_id=conflict.conflict_id,
                character_id=conflict.character_id,
                fact_type=conflict.fact_type,
                memory_ids=conflict.memory_ids,
                created_at=conflict.created_at,
                resolution=resolution,
                preferred_memory_id=preferred_memory_id,
            )
            store.snapshot_version += 1


def approve_memory(
    store: MemoryStore,
    memory_id: str,
    *,
    approved_at: str | None = None,
    reviewer: str | None = None,
    decision_reference: str | None = None,
    supersede_memory_id: str | None = None,
) -> MemoryRecord:
    current = store.get(memory_id)
    explicitly_correcting = (
        current.status == MemoryStatus.REJECTED
        and current.approval_status == ApprovalStatus.PENDING
        and supersede_memory_id is not None
    )
    if current.status in {MemoryStatus.EXPIRED, MemoryStatus.ROLLED_BACK, MemoryStatus.INVALID} or (current.status == MemoryStatus.REJECTED and not explicitly_correcting):
        raise CharacterMemoryValidationError(f"cannot approve memory in {current.status.value} status")
    timestamp = approved_at or utc_now()
    parse_timestamp(timestamp, "approved_at")
    if supersede_memory_id == memory_id:
        raise CharacterMemoryValidationError("memory cannot supersede itself")
    superseded = None if supersede_memory_id is None else store.get(supersede_memory_id)
    if superseded is not None:
        if superseded.character_id != current.character_id or superseded.fact_type != current.fact_type:
            raise CharacterMemoryValidationError("approved correction must target the same character and fact type")
        if superseded.status not in {MemoryStatus.ACTIVE, MemoryStatus.PENDING}:
            raise CharacterMemoryValidationError("superseded memory is not active")
    primary = current.evidence[0]
    approval_evidence = create_evidence(
        evidence_type=EvidenceType.HUMAN_APPROVED,
        source_case_id=primary.source_case_id,
        source_segment_id=decision_reference or primary.source_segment_id,
        source_text_hash=primary.source_text_hash,
        excerpt=primary.excerpt,
        language=primary.language,
        observed_at=timestamp,
    )
    updated = replace(
        current,
        evidence=merge_evidence(current.evidence, (approval_evidence,)),
        evidence_type=EvidenceType.HUMAN_APPROVED,
        approval_status=ApprovalStatus.APPROVED,
        approval_metadata=ApprovalMetadata(current.value, timestamp, reviewer, decision_reference),
        status=MemoryStatus.ACTIVE,
        supersedes_memory_id=supersede_memory_id,
        updated_at=timestamp,
        version=current.version + 1,
    )
    validate_record(updated)
    store._update(updated)
    if superseded is not None:
        store._update(replace(superseded, status=MemoryStatus.SUPERSEDED, updated_at=timestamp, version=superseded.version + 1))
        _resolve_conflicts(store, memory_id, supersede_memory_id, "human_approved_correction")
    return updated


def reject_memory(
    store: MemoryStore,
    memory_id: str,
    *,
    rejected_at: str | None = None,
    reviewer: str | None = None,
    decision_reference: str | None = None,
) -> MemoryRecord:
    current = store.get(memory_id)
    if current.approval_status == ApprovalStatus.APPROVED:
        raise CharacterMemoryValidationError("approved memory requires a superseding correction, not automatic rejection")
    if current.status in {MemoryStatus.SUPERSEDED, MemoryStatus.EXPIRED, MemoryStatus.ROLLED_BACK, MemoryStatus.INVALID}:
        raise CharacterMemoryValidationError(f"cannot reject memory in {current.status.value} status")
    timestamp = rejected_at or utc_now()
    parse_timestamp(timestamp, "rejected_at")
    primary = current.evidence[0]
    rejected_evidence = create_evidence(
        evidence_type=EvidenceType.HUMAN_REJECTED,
        source_case_id=primary.source_case_id,
        source_segment_id=decision_reference or primary.source_segment_id,
        source_text_hash=primary.source_text_hash,
        excerpt=primary.excerpt,
        language=primary.language,
        observed_at=timestamp,
    )
    updated = replace(
        current,
        evidence=merge_evidence(current.evidence, (rejected_evidence,)),
        evidence_type=EvidenceType.HUMAN_REJECTED,
        approval_status=ApprovalStatus.REJECTED,
        approval_metadata=None,
        status=MemoryStatus.REJECTED,
        updated_at=timestamp,
        version=current.version + 1,
    )
    validate_record(updated)
    store._update(updated)
    return updated


def supersede_memory(
    store: MemoryStore,
    memory_id: str,
    *,
    superseded_by_memory_id: str,
    updated_at: str | None = None,
) -> MemoryRecord:
    current = store.get(memory_id)
    replacement = store.get(superseded_by_memory_id)
    if memory_id == superseded_by_memory_id:
        raise CharacterMemoryValidationError("memory cannot supersede itself")
    if current.character_id != replacement.character_id or current.fact_type != replacement.fact_type:
        raise CharacterMemoryValidationError("supersede requires same character and fact type")
    if replacement.approval_status != ApprovalStatus.APPROVED:
        raise CharacterMemoryValidationError("replacement must be human-approved")
    timestamp = updated_at or utc_now()
    updated = replace(current, status=MemoryStatus.SUPERSEDED, updated_at=timestamp, version=current.version + 1)
    store._update(updated)
    _resolve_conflicts(store, superseded_by_memory_id, memory_id, "explicit_supersede")
    return updated


def expire_memory(store: MemoryStore, memory_id: str, *, expired_at: str | None = None) -> MemoryRecord:
    current = store.get(memory_id)
    if current.status not in {MemoryStatus.ACTIVE, MemoryStatus.PENDING}:
        raise CharacterMemoryValidationError("only active or pending memory can expire")
    timestamp = expired_at or utc_now()
    parse_timestamp(timestamp, "expired_at")
    updated = replace(current, status=MemoryStatus.EXPIRED, updated_at=timestamp, version=current.version + 1)
    store._update(updated)
    return updated


def rollback_memory(
    store: MemoryStore,
    memory_id: str,
    *,
    target_version: int | None = None,
    rolled_back_at: str | None = None,
) -> MemoryRecord:
    current = store.get(memory_id)
    history = list(store.history.get(memory_id, []))
    if not history:
        raise CharacterMemoryValidationError("no prior version available for rollback")
    candidates = history if target_version is None else [item for item in history if item.version == target_version]
    if not candidates:
        raise CharacterMemoryValidationError("invalid rollback target version")
    target = candidates[-1]
    timestamp = rolled_back_at or utc_now()
    parse_timestamp(timestamp, "rolled_back_at")

    superseded = None
    superseded_target = None
    if current.supersedes_memory_id:
        superseded = store.get(current.supersedes_memory_id)
        old_history = list(store.history.get(superseded.memory_id, []))
        if superseded.status != MemoryStatus.SUPERSEDED or not old_history:
            raise CharacterMemoryValidationError("approved correction rollback has no restorable superseded version")
        superseded_target = old_history[-1]

    if superseded is not None and superseded_target is not None:
        restored_old = replace(
            superseded_target,
            evidence=merge_evidence(superseded_target.evidence, superseded.evidence),
            updated_at=timestamp,
            version=superseded.version + 1,
        )
        validate_record(restored_old)
        store._update(restored_old)
        rolled_back = replace(
            current,
            status=MemoryStatus.ROLLED_BACK,
            updated_at=timestamp,
            version=current.version + 1,
        )
        store._update(rolled_back)
        _resolve_conflicts(store, superseded.memory_id, memory_id, "approved_correction_rolled_back")
        return rolled_back

    restored = replace(
        target,
        evidence=merge_evidence(target.evidence, current.evidence),
        updated_at=timestamp,
        version=current.version + 1,
    )
    validate_record(restored)
    store._update(restored)
    return restored
