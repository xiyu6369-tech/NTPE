from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .deduplication import conflict_id, conflict_key, evidence_rank, fact_key, merge_evidence, strongest_evidence_type
from .models import (
    AddDisposition,
    AddResult,
    ApprovalMetadata,
    ApprovalStatus,
    ConflictRecord,
    Evidence,
    EvidenceType,
    ExpiryKind,
    ExpiryPolicy,
    FactType,
    MemoryRecord,
    MemoryStatus,
    SCHEMA_VERSION,
)
from .normalization import normalize_text, stable_evidence_id, stable_memory_id
from .validation import CharacterMemoryValidationError, validate_evidence, validate_memory_store, validate_record, validate_store_payload


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class MemoryStore:
    def __init__(self) -> None:
        self.schema_version = SCHEMA_VERSION
        self.records: dict[str, MemoryRecord] = {}
        self.history: dict[str, list[MemoryRecord]] = {}
        self.conflicts: dict[str, ConflictRecord] = {}
        self.snapshot_version = 0
        self._fact_index: dict[tuple[str, str, str], str] = {}
        self._conflict_index: dict[tuple[str, str], set[str]] = {}

    def _rebuild_indexes(self) -> None:
        self._fact_index = {}
        self._conflict_index = {}
        for record in sorted(self.records.values(), key=lambda item: item.memory_id):
            self._fact_index.setdefault(fact_key(record), record.memory_id)
            self._conflict_index.setdefault(conflict_key(record), set()).add(record.memory_id)

    def get(self, memory_id: str) -> MemoryRecord:
        try:
            return self.records[memory_id]
        except KeyError as exc:
            raise CharacterMemoryValidationError(f"unknown memory_id: {memory_id}") from exc

    def active_records(self) -> tuple[MemoryRecord, ...]:
        return tuple(sorted((record for record in self.records.values() if record.status == MemoryStatus.ACTIVE), key=lambda item: item.memory_id))

    def _insert(self, record: MemoryRecord) -> None:
        validate_record(record)
        if record.memory_id in self.records:
            raise CharacterMemoryValidationError(f"memory_id already exists: {record.memory_id}")
        self.records[record.memory_id] = record
        self.history.setdefault(record.memory_id, [])
        self._fact_index.setdefault(fact_key(record), record.memory_id)
        self._conflict_index.setdefault(conflict_key(record), set()).add(record.memory_id)
        self.snapshot_version += 1

    def _update(self, record: MemoryRecord) -> None:
        validate_record(record)
        current = self.get(record.memory_id)
        if record.version != current.version + 1:
            raise CharacterMemoryValidationError("updated record version must increment exactly once")
        self.history.setdefault(record.memory_id, []).append(current)
        self.records[record.memory_id] = record
        old_fact_key = fact_key(current)
        if old_fact_key != fact_key(record) and self._fact_index.get(old_fact_key) == record.memory_id:
            self._fact_index.pop(old_fact_key, None)
        self._fact_index.setdefault(fact_key(record), record.memory_id)
        self._conflict_index.setdefault(conflict_key(record), set()).add(record.memory_id)
        self.snapshot_version += 1

    def _set_conflict(self, conflict: ConflictRecord) -> None:
        self.conflicts[conflict.conflict_id] = conflict
        self.snapshot_version += 1

    def unresolved_memory_ids(self) -> set[str]:
        return {memory_id for conflict in self.conflicts.values() if conflict.unresolved for memory_id in conflict.memory_ids}

    def snapshot(self) -> dict[str, Any]:
        return self.to_dict()

    def restore_snapshot(self, payload: Mapping[str, Any]) -> None:
        restored = self.from_dict(payload)
        self.schema_version = restored.schema_version
        self.records = dict(restored.records)
        self.history = {key: list(items) for key, items in restored.history.items()}
        self.conflicts = dict(restored.conflicts)
        self.snapshot_version = restored.snapshot_version
        self._rebuild_indexes()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "records": [self.records[key].to_dict() for key in sorted(self.records)],
            "history": {key: [item.to_dict() for item in sorted(self.history.get(key, []), key=lambda record: record.version)] for key in sorted(self.history)},
            "conflicts": [self.conflicts[key].to_dict() for key in sorted(self.conflicts)],
            "snapshot_version": self.snapshot_version,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MemoryStore":
        validate_store_payload(payload)
        store = cls()
        store.records = {}
        for item in payload["records"]:
            record = MemoryRecord.from_dict(item)
            validate_record(record)
            if record.memory_id in store.records:
                raise CharacterMemoryValidationError("duplicate memory_id in serialized store")
            store.records[record.memory_id] = record
        store.history = {}
        for memory_id, versions in payload["history"].items():
            validate_memory_id = str(memory_id)
            if validate_memory_id not in store.records:
                raise CharacterMemoryValidationError("history references unknown memory_id")
            parsed = [MemoryRecord.from_dict(item) for item in versions]
            for record in parsed:
                validate_record(record)
                if record.memory_id != validate_memory_id:
                    raise CharacterMemoryValidationError("history record memory_id mismatch")
            if [record.version for record in parsed] != sorted({record.version for record in parsed}):
                raise CharacterMemoryValidationError("history versions must be unique and ordered")
            store.history[validate_memory_id] = parsed
        for memory_id in store.records:
            store.history.setdefault(memory_id, [])
        store.conflicts = {}
        for item in payload["conflicts"]:
            conflict = ConflictRecord.from_dict(item)
            if not set(conflict.memory_ids) <= set(store.records):
                raise CharacterMemoryValidationError("conflict references unknown memory")
            store.conflicts[conflict.conflict_id] = conflict
        store.snapshot_version = int(payload["snapshot_version"])
        store._rebuild_indexes()
        report = validate_memory_store(store)
        if not report["valid"]:
            raise CharacterMemoryValidationError("; ".join(report["errors"]))
        return store


def create_evidence(
    *,
    evidence_type: EvidenceType | str,
    source_case_id: str,
    source_segment_id: str,
    source_text_hash: str,
    excerpt: str,
    language: str,
    observed_at: str | None = None,
    evidence_id: str | None = None,
) -> Evidence:
    kind = evidence_type if isinstance(evidence_type, EvidenceType) else EvidenceType(evidence_type)
    timestamp = observed_at or utc_now()
    item = Evidence(
        evidence_id=evidence_id or stable_evidence_id(kind.value, source_case_id, source_segment_id, source_text_hash, excerpt),
        evidence_type=kind,
        source_case_id=normalize_text(source_case_id),
        source_segment_id=normalize_text(source_segment_id),
        source_text_hash=source_text_hash.lower(),
        excerpt=normalize_text(excerpt),
        language=normalize_text(language),
        observed_at=timestamp,
    )
    validate_evidence(item)
    return item


def default_expiry_for_fact(fact_type: FactType) -> ExpiryPolicy:
    if fact_type in {FactType.TEMPORAL_STATE, FactType.LOCATION_STATE}:
        return ExpiryPolicy(ExpiryKind.MANUAL_REVIEW_REQUIRED)
    return ExpiryPolicy(ExpiryKind.NEVER)


def create_memory(
    *,
    character_id: str,
    fact_type: FactType | str,
    value: str,
    evidence: Evidence | Iterable[Evidence],
    confidence: float,
    approval_status: ApprovalStatus | str = ApprovalStatus.PENDING,
    source_language: str | None = None,
    created_at: str | None = None,
    updated_at: str | None = None,
    expiry_policy: ExpiryPolicy | None = None,
    status: MemoryStatus | str = MemoryStatus.ACTIVE,
    approval_metadata: ApprovalMetadata | None = None,
    unresolved_identity: bool | None = None,
    supersedes_memory_id: str | None = None,
    memory_id: str | None = None,
) -> MemoryRecord:
    facts = fact_type if isinstance(fact_type, FactType) else FactType(fact_type)
    approval = approval_status if isinstance(approval_status, ApprovalStatus) else ApprovalStatus(approval_status)
    memory_status = status if isinstance(status, MemoryStatus) else MemoryStatus(status)
    evidence_items = (evidence,) if isinstance(evidence, Evidence) else tuple(evidence)
    if not evidence_items:
        raise CharacterMemoryValidationError("create_memory requires evidence")
    timestamp = created_at or utc_now()
    updated = updated_at or timestamp
    primary = evidence_items[0]
    normalized_character_id = normalize_text(character_id)
    normalized_value = normalize_text(value)
    record = MemoryRecord(
        memory_id=memory_id or stable_memory_id(normalized_character_id, facts.value, normalized_value, primary.evidence_id),
        character_id=normalized_character_id,
        fact_type=facts,
        value=normalized_value,
        evidence=merge_evidence(evidence_items),
        evidence_type=primary.evidence_type,
        confidence=float(confidence),
        approval_status=approval,
        source_language=normalize_text(source_language or primary.language),
        source_case_id=primary.source_case_id,
        source_segment_id=primary.source_segment_id,
        created_at=timestamp,
        updated_at=updated,
        version=1,
        expiry_policy=expiry_policy or default_expiry_for_fact(facts),
        status=memory_status,
        approval_metadata=approval_metadata,
        unresolved_identity=normalized_character_id.startswith("unresolved:") if unresolved_identity is None else bool(unresolved_identity),
        supersedes_memory_id=supersedes_memory_id,
    )
    validate_record(record)
    return record


def _merged_record(existing: MemoryRecord, incoming: MemoryRecord, timestamp: str) -> MemoryRecord:
    evidence = merge_evidence(existing.evidence, incoming.evidence)
    incoming_rank = evidence_rank(incoming)
    existing_rank = evidence_rank(existing)
    approval_status = incoming.approval_status if incoming_rank > existing_rank else existing.approval_status
    approval_metadata = incoming.approval_metadata if incoming_rank > existing_rank else existing.approval_metadata
    return replace(
        existing,
        evidence=evidence,
        evidence_type=strongest_evidence_type(evidence),
        confidence=max(existing.confidence, incoming.confidence),
        approval_status=approval_status,
        approval_metadata=approval_metadata,
        status=MemoryStatus.ACTIVE,
        updated_at=timestamp,
        version=existing.version + 1,
    )


def add_or_merge_memory(store: MemoryStore, record: MemoryRecord, *, now: str | None = None) -> AddResult:
    validate_record(record)
    timestamp = now or utc_now()
    existing_id_record = store.records.get(record.memory_id)
    if existing_id_record is not None and existing_id_record.status not in {MemoryStatus.ACTIVE, MemoryStatus.PENDING}:
        return AddResult(AddDisposition.REJECTED, existing_id_record, message=f"existing canonical memory is {existing_id_record.status.value}")
    same_id = store._fact_index.get(fact_key(record))
    same = [] if same_id is None else [store.records[same_id]]
    same = [item for item in same if item.status in {MemoryStatus.ACTIVE, MemoryStatus.PENDING}]
    if same:
        existing = sorted(same, key=lambda item: (-evidence_rank(item), item.memory_id))[0]
        existing_evidence = {item.evidence_id for item in existing.evidence}
        incoming_evidence = {item.evidence_id for item in record.evidence}
        if incoming_evidence <= existing_evidence:
            return AddResult(AddDisposition.DUPLICATE, existing, message="canonical fact and evidence already exist")
        merged = _merged_record(existing, record, timestamp)
        store._update(merged)
        return AddResult(AddDisposition.MERGED, merged, message="additional evidence merged into canonical fact")

    competing = [store.records[memory_id] for memory_id in sorted(store._conflict_index.get(conflict_key(record), set())) if store.records[memory_id].status in {MemoryStatus.ACTIVE, MemoryStatus.PENDING}]
    if not competing:
        store._insert(record)
        return AddResult(AddDisposition.ACCEPTED, record)

    max_existing = max(competing, key=lambda item: (evidence_rank(item), item.memory_id))
    old_rank = evidence_rank(max_existing)
    new_rank = evidence_rank(record)
    ids = tuple(sorted({item.memory_id for item in competing} | {record.memory_id}))
    conflict = ConflictRecord(
        conflict_id=conflict_id(record.character_id, record.fact_type.value, ids),
        character_id=record.character_id,
        fact_type=record.fact_type,
        memory_ids=ids,
        created_at=timestamp,
    )
    if old_rank > new_rank:
        rejected = replace(record, status=MemoryStatus.REJECTED, updated_at=timestamp)
        store._insert(rejected)
        resolved = replace(conflict, resolution="evidence_precedence", preferred_memory_id=max_existing.memory_id)
        store._set_conflict(resolved)
        return AddResult(AddDisposition.REJECTED, rejected, resolved, "higher evidence tier retained")
    if new_rank > old_rank:
        store._insert(record)
        for existing in competing:
            store._update(replace(existing, status=MemoryStatus.SUPERSEDED, updated_at=timestamp, version=existing.version + 1))
        resolved = replace(conflict, resolution="evidence_precedence", preferred_memory_id=record.memory_id)
        store._set_conflict(resolved)
        return AddResult(AddDisposition.SUPERSEDED, record, resolved, "higher evidence tier superseded lower-tier values")

    store._insert(record)
    store._set_conflict(conflict)
    return AddResult(AddDisposition.CONFLICT, record, conflict, "same-tier conflicting values require explicit resolution")
