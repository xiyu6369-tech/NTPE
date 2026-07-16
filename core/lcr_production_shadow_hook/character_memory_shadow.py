from __future__ import annotations

import hashlib
import json
import time
from dataclasses import replace
from types import MappingProxyType
from typing import Mapping, Sequence

from core.character_memory_v2 import (
    ApprovalStatus,
    EvidenceType,
    MemoryStatus,
    MemoryStore,
    select_prompt_eligible_memories,
    validate_memory_store,
)

from .models import CharacterMemoryShadowInput, CharacterMemoryShadowResult


DEFAULT_SHADOW_SELECTION_BUDGET = 128
SUPPORTED_PROFILES = {
    ("ko", "zh-Hant"): {"source_languages": ("ko",)},
    ("ja", "zh-Hant"): {"source_languages": ("ja",)},
    ("en", "zh-Hant"): {"source_languages": ("en",)},
}


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _invalid_identifier(value: str) -> bool:
    return not value or "/" in value or "\\" in value or value in {".", ".."}


def build_character_memory_shadow_input(
    store: MemoryStore,
    *,
    document_id: str,
    chunk_index: int,
    source_language: str,
    target_language: str,
    character_ids: Sequence[str],
    snapshot_id: str,
    scope: Mapping[str, str] | None = None,
    token_budget: int = DEFAULT_SHADOW_SELECTION_BUDGET,
    created_at: str = "",
) -> CharacterMemoryShadowInput:
    """Create the defensive immutable view before a bounded worker is submitted."""
    if not isinstance(store, MemoryStore):
        raise ValueError("character_memory_store must be MemoryStore")
    if any(_invalid_identifier(str(item)) for item in (document_id, snapshot_id, *character_ids)):
        raise ValueError("character memory identifiers cannot contain path traversal or separators")
    if not isinstance(chunk_index, int) or isinstance(chunk_index, bool) or chunk_index < 0:
        raise ValueError("chunk_index must be a non-negative integer")
    if not isinstance(token_budget, int) or isinstance(token_budget, bool) or token_budget < 0:
        raise ValueError("token_budget must be a non-negative integer")
    report = validate_memory_store(store)
    if not report["valid"]:
        raise ValueError("invalid character memory store")
    payload = store.to_dict()
    fingerprint = _canonical_hash(payload)
    # Round-trip through the public schema so no mutable store dictionary/list is retained.
    copied = MemoryStore.from_dict(json.loads(json.dumps(payload, ensure_ascii=False)))
    selected_characters = set(str(item) for item in character_ids)
    selected_records = [
        record for record in copied.records.values()
        if record.character_id in selected_characters
    ]
    # Selection needs the fact value and evidence type, but never an evidence
    # excerpt. Keep the detached record contract while redacting source prose.
    records = tuple(
        replace(record, evidence=tuple(replace(item, excerpt="[redacted]") for item in record.evidence))
        for record in sorted(selected_records, key=lambda item: item.memory_id)
    )
    selected_ids = {record.memory_id for record in records}
    conflicts = tuple(
        conflict for conflict in sorted(copied.conflicts.values(), key=lambda item: item.conflict_id)
        if set(conflict.memory_ids) <= selected_ids
    )
    frozen_scope = MappingProxyType({str(key): str(value) for key, value in sorted((scope or {}).items())})
    return CharacterMemoryShadowInput(
        document_id=str(document_id), chunk_index=chunk_index,
        source_language=str(source_language), target_language=str(target_language),
        character_ids=tuple(sorted(set(str(item) for item in character_ids))),
        snapshot_id=str(snapshot_id), schema_version=str(copied.schema_version),
        store_fingerprint=fingerprint, scope=frozen_scope, token_budget=token_budget,
        created_at=str(created_at), records=records, conflicts=conflicts,
    )


def _working_store(snapshot: CharacterMemoryShadowInput) -> MemoryStore:
    store = MemoryStore()
    store.records = {record.memory_id: record for record in snapshot.records}
    store.history = {record.memory_id: [] for record in snapshot.records}
    store.conflicts = {conflict.conflict_id: conflict for conflict in snapshot.conflicts}
    store.snapshot_version = 0
    store._rebuild_indexes()
    return store


def _empty(snapshot: CharacterMemoryShadowInput, status: str, *, duration_ms: float = 0.0) -> CharacterMemoryShadowResult:
    return CharacterMemoryShadowResult(
        module="character_memory", status=status, snapshot_id=snapshot.snapshot_id,
        store_fingerprint=snapshot.store_fingerprint, selected_memory_ids=(), selected_fact_types=(),
        selected_character_ids=(), selected_fingerprint=_canonical_hash([]), estimated_tokens=0,
        token_budget=snapshot.token_budget, available_count=len(snapshot.records), eligible_count=0,
        selected_count=0, dropped_count=len(snapshot.records), drop_reasons=MappingProxyType({}),
        dedup_savings=0, conflict_count=sum(1 for item in snapshot.conflicts if item.unresolved),
        unresolved_identity_count=sum(1 for item in snapshot.records if item.unresolved_identity),
        expired_count=sum(1 for item in snapshot.records if item.status == MemoryStatus.EXPIRED),
        inference_excluded_count=sum(1 for item in snapshot.records if item.evidence_type == EvidenceType.AI_INFERENCE),
        human_approved_count=sum(1 for item in snapshot.records if item.approval_status == ApprovalStatus.APPROVED),
        duration_ms=duration_ms,
    )


def empty_character_memory_result(
    *,
    status: str,
    snapshot_id: str = "",
    store_fingerprint: str = "",
    token_budget: int = DEFAULT_SHADOW_SELECTION_BUDGET,
) -> CharacterMemoryShadowResult:
    """Return a safe redacted child result when metadata is absent or invalid."""
    empty_hash = _canonical_hash([])
    return CharacterMemoryShadowResult(
        module="character_memory", status=status, snapshot_id=snapshot_id,
        store_fingerprint=store_fingerprint, selected_memory_ids=(), selected_fact_types=(),
        selected_character_ids=(), selected_fingerprint=empty_hash, estimated_tokens=0,
        token_budget=token_budget, available_count=0, eligible_count=0, selected_count=0,
        dropped_count=0, drop_reasons=MappingProxyType({}), dedup_savings=0,
        conflict_count=0, unresolved_identity_count=0, expired_count=0,
        inference_excluded_count=0, human_approved_count=0,
    )


def evaluate_character_memory_shadow(
    snapshot: CharacterMemoryShadowInput,
    *,
    now: str | None = None,
) -> CharacterMemoryShadowResult:
    """Call only Batch 2 validation/selection APIs and return redacted planning evidence."""
    started = time.perf_counter_ns()
    profile = SUPPORTED_PROFILES.get((snapshot.source_language, snapshot.target_language))
    if profile is None:
        return _empty(snapshot, "invalid")
    if not snapshot.character_ids:
        return _empty(snapshot, "no_eligible_memory")
    store = _working_store(snapshot)
    report = validate_memory_store(store)
    if not report["valid"] or _canonical_hash(store.to_dict()) == "":
        return _empty(snapshot, "invalid")
    selected = select_prompt_eligible_memories(
        store, character_ids=snapshot.character_ids, token_budget=snapshot.token_budget,
        language_profile=profile, include_pending=False, scope=snapshot.scope, now=now,
    )
    items = selected.items
    selected_view = [
        {"memory_id": item.memory_id, "character_id": item.character_id,
         "fact_type": item.fact_type.value, "estimated_tokens": item.estimated_tokens}
        for item in items
    ]
    excluded = dict(selected.excluded_counts)
    selected_ids = {item.memory_id for item in items}
    eligible_count = len(items) + excluded.get("budget", 0)
    warnings = any(key in excluded for key in ("unresolved_conflict", "unresolved_identity", "expired", "expiry_or_scope"))
    status = "selected" if items else "no_eligible_memory"
    if warnings:
        status = "completed_with_warnings"
    elif excluded.get("budget", 0):
        status = "budget_limited"
    duration_ms = max(0.0, (time.perf_counter_ns() - started) / 1_000_000)
    return CharacterMemoryShadowResult(
        module="character_memory", status=status, snapshot_id=snapshot.snapshot_id,
        store_fingerprint=snapshot.store_fingerprint,
        selected_memory_ids=tuple(item.memory_id for item in items),
        selected_fact_types=tuple(item.fact_type.value for item in items),
        selected_character_ids=tuple(item.character_id for item in items),
        selected_fingerprint=_canonical_hash(selected_view), estimated_tokens=selected.estimated_tokens,
        token_budget=selected.token_budget, available_count=len(snapshot.records),
        eligible_count=eligible_count, selected_count=len(items),
        dropped_count=max(0, len(snapshot.records) - len(items)),
        drop_reasons=MappingProxyType(dict(sorted(excluded.items()))),
        dedup_savings=excluded.get("duplicate", 0),
        conflict_count=excluded.get("unresolved_conflict", 0),
        unresolved_identity_count=excluded.get("unresolved_identity", 0),
        expired_count=(sum(1 for item in snapshot.records if item.status == MemoryStatus.EXPIRED)
                       + excluded.get("expiry_or_scope", 0)),
        inference_excluded_count=excluded.get("ai_inference", 0),
        human_approved_count=sum(1 for item in items if store.records[item.memory_id].approval_status == ApprovalStatus.APPROVED),
        cache_identity_impact_planned=bool(selected_ids), cache_identity_applied=False,
        duration_ms=round(duration_ms, 6),
    )
