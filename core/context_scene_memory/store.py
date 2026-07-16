from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .models import (
    AddDisposition, AddResult, ApprovalStatus, ContextEvidence, ContextMemoryRecord,
    ContextType, EvidenceType, ExpiryKind, ExpiryPolicy, RecordStatus,
    ResolutionStatus, SceneMemoryRecord, UnresolvedReference, SCHEMA_VERSION,
)
from .normalization import normalize_text, stable_id
from .validation import ContextSceneValidationError, validate_context_record, validate_context_store, validate_evidence, validate_scene_record


EVIDENCE_PRIORITY = {
    EvidenceType.HUMAN_REJECTED: 0,
    EvidenceType.AI_INFERENCE: 10,
    EvidenceType.HISTORICAL_IMPORT: 20,
    EvidenceType.RULE_DERIVED: 30,
    EvidenceType.TRANSLATION_OBSERVATION: 40,
    EvidenceType.SOURCE_OBSERVATION: 50,
    EvidenceType.HUMAN_APPROVED: 60,
}

SINGULAR_CONTEXT_TYPES = {
    ContextType.LOCATION_STATE,
    ContextType.TEMPORAL_STATE,
    ContextType.SPEAKER_STATE,
    ContextType.POINT_OF_VIEW,
    ContextType.RELATIONSHIP_STATE,
    ContextType.ADDRESSING_STATE,
    ContextType.TERMINOLOGY_STATE,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _merge_evidence(*groups: Iterable[ContextEvidence]) -> tuple[ContextEvidence, ...]:
    items = {item.evidence_id: item for group in groups for item in group}
    return tuple(items[key] for key in sorted(items))


def _rank(record: ContextMemoryRecord) -> int:
    return max(EVIDENCE_PRIORITY[item.evidence_type] for item in record.evidence)


def _fact_key(record: ContextMemoryRecord) -> tuple[str | None, str | None, str, str]:
    return record.chapter_id, record.scene_id, record.context_type.value, normalize_text(record.value).casefold()


def _conflict_key(record: ContextMemoryRecord) -> tuple[str | None, str | None, str]:
    return record.chapter_id, record.scene_id, record.context_type.value


class ContextMemoryStore:
    def __init__(self) -> None:
        self.schema_version = SCHEMA_VERSION
        self.contexts: dict[str, ContextMemoryRecord] = {}
        self.scenes: dict[str, SceneMemoryRecord] = {}
        self.context_history: dict[str, list[ContextMemoryRecord]] = {}
        self.scene_history: dict[str, list[SceneMemoryRecord]] = {}
        self.conflicts: dict[str, tuple[str, ...]] = {}
        self.snapshot_version = 0

    def get_context(self, context_id: str) -> ContextMemoryRecord:
        try:
            return self.contexts[context_id]
        except KeyError as exc:
            raise ContextSceneValidationError(f"unknown context_id: {context_id}") from exc

    def get_scene(self, scene_id: str) -> SceneMemoryRecord:
        try:
            return self.scenes[scene_id]
        except KeyError as exc:
            raise ContextSceneValidationError(f"unknown scene_id: {scene_id}") from exc

    def _insert_context(self, record: ContextMemoryRecord) -> None:
        validate_context_record(record)
        if record.context_id in self.contexts:
            raise ContextSceneValidationError("context_id already exists")
        self.contexts[record.context_id] = record
        self.context_history.setdefault(record.context_id, [])
        self.snapshot_version += 1

    def _update_context(self, record: ContextMemoryRecord) -> None:
        validate_context_record(record)
        current = self.get_context(record.context_id)
        if record.version != current.version + 1:
            raise ContextSceneValidationError("context version must increment exactly once")
        self.context_history.setdefault(record.context_id, []).append(current)
        self.contexts[record.context_id] = record
        self.snapshot_version += 1

    def _insert_scene(self, scene: SceneMemoryRecord) -> None:
        validate_scene_record(scene)
        if scene.scene_id in self.scenes:
            raise ContextSceneValidationError("scene_id already exists")
        self.scenes[scene.scene_id] = scene
        self.scene_history.setdefault(scene.scene_id, [])
        self.snapshot_version += 1

    def _update_scene(self, scene: SceneMemoryRecord) -> None:
        validate_scene_record(scene)
        current = self.get_scene(scene.scene_id)
        if scene.scene_version != current.scene_version + 1:
            raise ContextSceneValidationError("scene version must increment exactly once")
        self.scene_history.setdefault(scene.scene_id, []).append(current)
        self.scenes[scene.scene_id] = scene
        self.snapshot_version += 1

    def unresolved_conflict_ids(self) -> set[str]:
        return {item for ids in self.conflicts.values() for item in ids}

    def snapshot(self) -> dict[str, Any]:
        return self.to_dict()

    def restore(self, payload: Mapping[str, Any]) -> None:
        restored = self.from_dict(payload)
        self.schema_version = restored.schema_version
        self.contexts = dict(restored.contexts)
        self.scenes = dict(restored.scenes)
        self.context_history = {key: list(value) for key, value in restored.context_history.items()}
        self.scene_history = {key: list(value) for key, value in restored.scene_history.items()}
        self.conflicts = dict(restored.conflicts)
        self.snapshot_version = restored.snapshot_version

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contexts": [self.contexts[key].to_dict() for key in sorted(self.contexts)],
            "scenes": [self.scenes[key].to_dict() for key in sorted(self.scenes)],
            "context_history": {key: [item.to_dict() for item in self.context_history.get(key, [])] for key in sorted(self.context_history)},
            "scene_history": {key: [item.to_dict() for item in self.scene_history.get(key, [])] for key in sorted(self.scene_history)},
            "conflicts": {key: list(self.conflicts[key]) for key in sorted(self.conflicts)},
            "snapshot_version": self.snapshot_version,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ContextMemoryStore":
        required = {"schema_version", "contexts", "scenes", "context_history", "scene_history", "conflicts", "snapshot_version"}
        if set(payload) != required or payload.get("schema_version") != SCHEMA_VERSION:
            raise ContextSceneValidationError("unknown schema version or invalid store fields")
        store = cls()
        try:
            for data in payload["contexts"]:
                record = ContextMemoryRecord.from_dict(data)
                if record.context_id in store.contexts:
                    raise ContextSceneValidationError("duplicate serialized context_id")
                store.contexts[record.context_id] = record
            for data in payload["scenes"]:
                scene = SceneMemoryRecord.from_dict(data)
                if scene.scene_id in store.scenes:
                    raise ContextSceneValidationError("duplicate serialized scene_id")
                store.scenes[scene.scene_id] = scene
            store.context_history = {str(key): [ContextMemoryRecord.from_dict(item) for item in values] for key, values in payload["context_history"].items()}
            store.scene_history = {str(key): [SceneMemoryRecord.from_dict(item) for item in values] for key, values in payload["scene_history"].items()}
            store.conflicts = {str(key): tuple(str(item) for item in values) for key, values in payload["conflicts"].items()}
            store.snapshot_version = int(payload["snapshot_version"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ContextSceneValidationError("invalid context store payload") from exc
        if not validate_context_store(store)["valid"]:
            raise ContextSceneValidationError("serialized context store failed validation")
        return store


def create_context_evidence(
    *, evidence_type: EvidenceType | str, source_case_id: str, source_segment_id: str,
    excerpt: str, language: str, source_text_hash: str | None = None,
    translation_text_hash: str | None = None, rule_id: str | None = None,
    observed_at: str | None = None, evidence_id: str | None = None,
) -> ContextEvidence:
    kind = evidence_type if isinstance(evidence_type, EvidenceType) else EvidenceType(evidence_type)
    timestamp = observed_at or utc_now()
    normalized_excerpt = normalize_text(excerpt)
    item = ContextEvidence(
        evidence_id or stable_id("ctxev", kind.value, source_case_id, source_segment_id, source_text_hash, translation_text_hash, normalized_excerpt),
        kind, normalize_text(source_case_id), normalize_text(source_segment_id),
        None if source_text_hash is None else source_text_hash.lower(),
        None if translation_text_hash is None else translation_text_hash.lower(),
        normalized_excerpt, normalize_text(language), None if rule_id is None else normalize_text(rule_id), timestamp,
    )
    validate_evidence(item)
    return item


def default_expiry(context_type: ContextType, scene_id: str | None, chapter_id: str | None) -> ExpiryPolicy:
    if context_type in {ContextType.PREVIOUS_TRANSLATION_EXCERPT, ContextType.EVENT_STATE, ContextType.TEMPORAL_STATE, ContextType.LOCATION_STATE, ContextType.SPEAKER_STATE, ContextType.UNRESOLVED_REFERENCE}:
        if scene_id:
            return ExpiryPolicy(ExpiryKind.SCENE_SCOPE, scene_id)
        return ExpiryPolicy(ExpiryKind.MANUAL_REVIEW_REQUIRED)
    if context_type == ContextType.SCENE_SUMMARY and chapter_id:
        return ExpiryPolicy(ExpiryKind.CHAPTER_SCOPE, chapter_id)
    return ExpiryPolicy(ExpiryKind.NEVER)


def create_context_memory(
    *, context_type: ContextType | str, value: str, evidence: ContextEvidence | Iterable[ContextEvidence],
    confidence: float, source_language: str | None = None, chapter_id: str | None = None,
    scene_id: str | None = None, sequence_index: int = 0, scope: str = "local",
    approval_status: ApprovalStatus | str = ApprovalStatus.PENDING,
    expiry_policy: ExpiryPolicy | None = None, status: RecordStatus | str = RecordStatus.ACTIVE,
    created_at: str | None = None, updated_at: str | None = None,
    supersedes_context_id: str | None = None, experimental_only: bool = False,
    context_id: str | None = None,
) -> ContextMemoryRecord:
    kind = context_type if isinstance(context_type, ContextType) else ContextType(context_type)
    evidence_items = (evidence,) if isinstance(evidence, ContextEvidence) else tuple(evidence)
    if not evidence_items:
        raise ContextSceneValidationError("context requires evidence")
    timestamp = created_at or utc_now()
    value = normalize_text(value)
    primary = evidence_items[0]
    record = ContextMemoryRecord(
        context_id or stable_id("ctx", kind.value, value.casefold(), primary.evidence_id, chapter_id, scene_id),
        kind, value, _merge_evidence(evidence_items), float(confidence),
        approval_status if isinstance(approval_status, ApprovalStatus) else ApprovalStatus(approval_status),
        normalize_text(source_language or primary.language), primary.source_case_id, primary.source_segment_id,
        chapter_id, scene_id, sequence_index, normalize_text(scope), timestamp, updated_at or timestamp, 1,
        expiry_policy or default_expiry(kind, scene_id, chapter_id),
        status if isinstance(status, RecordStatus) else RecordStatus(status), supersedes_context_id, experimental_only,
    )
    validate_context_record(record)
    return record


def add_or_merge_context(store: ContextMemoryStore, record: ContextMemoryRecord, *, now: str | None = None) -> AddResult:
    validate_context_record(record)
    timestamp = now or utc_now()
    same = [item for item in store.contexts.values() if _fact_key(item) == _fact_key(record) and item.status in {RecordStatus.ACTIVE, RecordStatus.PENDING}]
    if same:
        existing = sorted(same, key=lambda item: item.context_id)[0]
        old_ids = {item.evidence_id for item in existing.evidence}
        if {item.evidence_id for item in record.evidence} <= old_ids:
            return AddResult(AddDisposition.DUPLICATE, existing)
        merged = replace(existing, evidence=_merge_evidence(existing.evidence, record.evidence), confidence=max(existing.confidence, record.confidence), updated_at=timestamp, version=existing.version + 1)
        store._update_context(merged)
        return AddResult(AddDisposition.MERGED, merged)
    competing = [] if record.context_type not in SINGULAR_CONTEXT_TYPES else [item for item in store.contexts.values() if _conflict_key(item) == _conflict_key(record) and item.status in {RecordStatus.ACTIVE, RecordStatus.PENDING}]
    if not competing:
        store._insert_context(record)
        return AddResult(AddDisposition.ACCEPTED, record)
    strongest = max(competing, key=lambda item: (_rank(item), item.context_id))
    ids = tuple(sorted({item.context_id for item in competing} | {record.context_id}))
    conflict_id = stable_id("conflict", *ids)
    if _rank(strongest) > _rank(record):
        rejected = replace(record, status=RecordStatus.REJECTED, updated_at=timestamp)
        store._insert_context(rejected)
        return AddResult(AddDisposition.REJECTED, rejected, ids)
    if _rank(record) > _rank(strongest):
        store._insert_context(record)
        for existing in competing:
            store._update_context(replace(existing, status=RecordStatus.SUPERSEDED, updated_at=timestamp, version=existing.version + 1))
        return AddResult(AddDisposition.SUPERSEDED, record, ids)
    store._insert_context(record)
    store.conflicts[conflict_id] = ids
    store.snapshot_version += 1
    return AddResult(AddDisposition.CONFLICT, record, ids)


def create_scene_memory(
    *, scene_id: str, chapter_id: str, evidence: ContextEvidence | Iterable[ContextEvidence],
    location: str | None = None, time_state: str | None = None,
    created_at: str | None = None, status: RecordStatus | str = RecordStatus.ACTIVE,
) -> SceneMemoryRecord:
    evidence_items = (evidence,) if isinstance(evidence, ContextEvidence) else tuple(evidence)
    if not evidence_items:
        raise ContextSceneValidationError("scene requires evidence")
    timestamp = created_at or utc_now()
    scene = SceneMemoryRecord(normalize_text(scene_id), 1, normalize_text(chapter_id), None if location is None else normalize_text(location), None if time_state is None else normalize_text(time_state), (), None, None, (), (), _merge_evidence(evidence_items), timestamp, timestamp, status if isinstance(status, RecordStatus) else RecordStatus(status))
    validate_scene_record(scene)
    return scene


def add_scene(store: ContextMemoryStore, scene: SceneMemoryRecord) -> SceneMemoryRecord:
    store._insert_scene(scene)
    return scene


def create_unresolved_reference(
    *, surface_form: str, reference_type: str, evidence: ContextEvidence | Iterable[ContextEvidence],
    confidence: float, scope: str, expiry: ExpiryPolicy, candidate_targets: Iterable[str] = (),
    resolution_status: ResolutionStatus | str = ResolutionStatus.UNRESOLVED,
    resolved_target: str | None = None, reference_id: str | None = None,
) -> UnresolvedReference:
    evidence_items = (evidence,) if isinstance(evidence, ContextEvidence) else tuple(evidence)
    primary = evidence_items[0] if evidence_items else None
    if primary is None:
        raise ContextSceneValidationError("unresolved reference requires evidence")
    item = UnresolvedReference(reference_id or stable_id("ref", surface_form, reference_type, primary.evidence_id), normalize_text(surface_form), normalize_text(reference_type), tuple(sorted(set(candidate_targets))), _merge_evidence(evidence_items), float(confidence), resolution_status if isinstance(resolution_status, ResolutionStatus) else ResolutionStatus(resolution_status), normalize_text(scope), expiry, resolved_target)
    # Reuse scene validation by direct invariants here.
    if not 0 <= item.confidence <= 1:
        raise ContextSceneValidationError("reference confidence out of range")
    if item.resolution_status in {ResolutionStatus.UNRESOLVED, ResolutionStatus.CANDIDATE} and item.resolved_target is not None:
        raise ContextSceneValidationError("unresolved reference cannot have target")
    return item
