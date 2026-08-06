"""RM-7.0 Knowledge Evolution Foundation — knowledge manager.

Orchestrates CRUD operations across the tiered store:
  - add / update / delete / lock / merge entities
  - alias management
  - candidate lifecycle (promote, reject)

No provider. No network. Pure offline CRUD.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .models import (
    AliasEntry,
    CandidateStatus,
    ConflictRecord,
    EntityType,
    KnowledgeEntity,
    LearningCandidate,
    PriorityLevel,
    Severity,
    utc_now_iso,
)
from .resolver import KnowledgeResolver
from .store import KnowledgeStore


class KnowledgeManager:
    """Central CRUD manager for the knowledge evolution system.

    All mutations go through the store. The resolver is used for
    read-path queries only.
    """

    def __init__(self, store_root: Optional[str] = None):
        self._store = KnowledgeStore(store_root)
        self._resolver = KnowledgeResolver(self._store)

    # ── Entity CRUD ─────────────────────────────────────────

    def add_entity(
        self,
        source: str,
        canonical: str,
        entity_type: EntityType,
        priority: PriorityLevel = PriorityLevel.USER,
        locked: bool = False,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None,
    ) -> KnowledgeEntity:
        entity = KnowledgeEntity(
            source=source,
            canonical=canonical,
            entity_type=entity_type,
            priority=priority,
            locked=locked,
            confidence=confidence,
            metadata=dict(metadata or {}),
        )

        kind = entity_kind(entity_type)
        entities = self._store.load_entities(priority, kind)
        existing_idx: Optional[int] = None
        for i, e in enumerate(entities):
            if e.source == source:
                existing_idx = i
                break

        if existing_idx is not None:
            entities[existing_idx] = entity
        else:
            entities.append(entity)

        self._store.save_entities(entities, priority, kind)
        self._resolver.invalidate()
        return entity

    def update_entity(
        self,
        source: str,
        canonical: Optional[str] = None,
        entity_type: Optional[EntityType] = None,
        locked: Optional[bool] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict] = None,
        force: bool = False,
    ) -> Optional[KnowledgeEntity]:
        existing = self._resolver.resolve(source)
        if existing is None:
            return None

        if existing.is_locked and not force:
            return None

        new_canonical = canonical if canonical is not None else existing.canonical
        new_type = entity_type if entity_type is not None else existing.entity_type
        new_locked = locked if locked is not None else existing.locked
        new_confidence = confidence if confidence is not None else existing.confidence
        new_meta = dict(existing.metadata, **(metadata or {}))

        updated = KnowledgeEntity(
            source=source,
            canonical=new_canonical,
            entity_type=new_type,
            priority=existing.priority,
            locked=new_locked,
            confidence=new_confidence,
            entity_id=existing.entity_id,
            metadata=new_meta,
            created_at=existing.created_at,
            updated_at=utc_now_iso(),
            version=existing.version + 1,
        )

        old_kind = entity_kind(existing.entity_type)
        new_kind = entity_kind(new_type)
        old_entities = self._store.load_entities(existing.priority, old_kind)
        old_entities = [e for e in old_entities if e.source != source]
        self._store.save_entities(old_entities, existing.priority, old_kind)

        new_entities = self._store.load_entities(existing.priority, new_kind)
        new_entities.append(updated)
        self._store.save_entities(new_entities, existing.priority, new_kind)
        self._resolver.invalidate()
        return updated

    def delete_entity(self, source: str) -> bool:
        self._resolver.invalidate()
        entity = self._resolver.resolve(source)
        if entity is None:
            return False

        if entity.is_locked:
            return False

        kind = entity_kind(entity.entity_type)
        entities = self._store.load_entities(entity.priority, kind)
        entities = [e for e in entities if e.source != source]
        self._store.save_entities(entities, entity.priority, kind)
        self._resolver.invalidate()
        return True

    def lock_entity(self, source: str) -> bool:
        self._resolver.invalidate()
        entity = self._resolver.resolve(source)
        if entity is None:
            return False

        return self.update_entity(source, locked=True, force=True) is not None

    def unlock_entity(self, source: str) -> bool:
        self._resolver.invalidate()
        entity = self._resolver.resolve(source)
        if entity is None:
            return False

        if entity.priority == PriorityLevel.USER:
            return False

        return self.update_entity(source, locked=False, force=True) is not None

    def get_entity(self, source: str) -> Optional[KnowledgeEntity]:
        return self._resolver.resolve(source)

    def get_canonical(self, source: str) -> str:
        return self._resolver.resolve_canonical(source)

    # ── Alias management ────────────────────────────────────

    def add_alias(
        self,
        alias: str,
        target: str,
        confidence: float = 0.95,
        priority: PriorityLevel = PriorityLevel.USER,
    ) -> AliasEntry:
        entry = AliasEntry(alias=alias, target=target, confidence=confidence)
        aliases = self._store.load_aliases(priority)
        aliases = [a for a in aliases if a.alias != alias]
        aliases.append(entry)
        self._store.save_aliases(aliases, priority)
        self._resolver.invalidate()
        return entry

    def remove_alias(self, alias: str, priority: PriorityLevel) -> bool:
        aliases = self._store.load_aliases(priority)
        new_aliases = [a for a in aliases if a.alias != alias]
        changed = len(new_aliases) != len(aliases)
        if changed:
            self._store.save_aliases(new_aliases, priority)
            self._resolver.invalidate()
        return changed

    def resolve_alias(self, alias: str) -> Optional[str]:
        entity = self._resolver.resolve(alias)
        return entity.canonical if entity else None

    # ── Candidate lifecycle ─────────────────────────────────

    def add_candidate(
        self,
        source: str,
        canonical: str,
        entity_type: EntityType = EntityType.CHARACTER,
        confidence: float = 0.5,
        context_hints: Optional[List[str]] = None,
    ) -> LearningCandidate:
        existing = self._resolver.resolve(source)
        if existing is not None:
            raise ValueError(f"Entity already exists for source '{source}'")

        candidate = LearningCandidate(
            source=source,
            canonical=canonical,
            entity_type=entity_type,
            confidence=confidence,
            occurrence_count=1,
            context_hints=context_hints or [],
        )

        candidates = self._store.load_candidates()
        for i, c in enumerate(candidates):
            if c.source == source:
                candidates[i] = LearningCandidate(
                    source=c.source,
                    canonical=c.canonical,
                    entity_type=c.entity_type,
                    confidence=max(c.confidence, confidence),
                    occurrence_count=c.occurrence_count + 1,
                    context_hints=c.context_hints,
                    status=c.status,
                    metadata=c.metadata,
                    created_at=c.created_at,
                    updated_at=utc_now_iso(),
                )
                self._store.save_candidates(candidates)
                return candidates[i]

        candidates.append(candidate)
        self._store.save_candidates(candidates)
        return candidate

    def promote_candidate(
        self,
        source: str,
        priority: PriorityLevel = PriorityLevel.LEARNING,
    ) -> Optional[KnowledgeEntity]:
        candidates = self._store.load_candidates()
        target_candidate: Optional[LearningCandidate] = None
        for c in candidates:
            if c.source == source:
                target_candidate = c
                break

        if target_candidate is None:
            return None

        entity = self.add_entity(
            source=source,
            canonical=target_candidate.canonical,
            entity_type=target_candidate.entity_type,
            priority=priority,
            confidence=target_candidate.confidence,
        )

        candidates = [
            LearningCandidate(
                source=c.source,
                canonical=c.canonical,
                entity_type=c.entity_type,
                confidence=c.confidence,
                occurrence_count=c.occurrence_count,
                context_hints=c.context_hints,
                status=CandidateStatus.PROMOTED,
                metadata={**c.metadata, "promoted_at": utc_now_iso()},
                created_at=c.created_at,
                updated_at=utc_now_iso(),
            )
            if c.source == source
            else c
            for c in candidates
        ]
        self._store.save_candidates(candidates)
        return entity

    def reject_candidate(self, source: str) -> bool:
        candidates = self._store.load_candidates()
        changed = False
        new_candidates: List[LearningCandidate] = []
        for c in candidates:
            if c.source == source:
                changed = True
                new_candidates.append(
                    LearningCandidate(
                        source=c.source,
                        canonical=c.canonical,
                        entity_type=c.entity_type,
                        confidence=c.confidence,
                        occurrence_count=c.occurrence_count,
                        context_hints=c.context_hints,
                        status=CandidateStatus.REJECTED,
                        metadata={**c.metadata, "rejected_at": utc_now_iso()},
                        created_at=c.created_at,
                        updated_at=utc_now_iso(),
                    )
                )
            else:
                new_candidates.append(c)

        if changed:
            self._store.save_candidates(new_candidates)
        return changed

    def list_candidates(self) -> List[LearningCandidate]:
        return self._store.load_candidates()

    # ── Conflict detection ──────────────────────────────────

    def detect_conflict(
        self,
        source: str,
        observed: str,
        entity_type: EntityType = EntityType.CHARACTER,
    ) -> Optional[ConflictRecord]:
        entity = self._resolver.resolve(source)
        if entity is None:
            return None

        if entity.canonical == observed:
            return None

        severity = Severity.HIGH
        if entity.is_locked:
            severity = Severity.HIGH
        elif entity.priority == PriorityLevel.LEARNING:
            severity = Severity.LOW

        return ConflictRecord(
            source=source,
            expected=entity.canonical,
            observed=observed,
            severity=severity,
            entity_type=entity_type,
        )

    # ── Snapshot ─────────────────────────────────────────────

    def snapshot(self) -> Dict:
        return self._store.snapshot()

    @property
    def store(self) -> KnowledgeStore:
        return self._store

    @property
    def resolver(self) -> KnowledgeResolver:
        return self._resolver


def _entity_kind(entity_type: EntityType) -> str:
    if entity_type in (EntityType.CHARACTER, EntityType.LOCATION, EntityType.ORGANIZATION, EntityType.TITLE, EntityType.ALIAS):
        return "characters"
    return "glossary"


def entity_kind(entity_type: EntityType) -> str:
    return _entity_kind(entity_type)