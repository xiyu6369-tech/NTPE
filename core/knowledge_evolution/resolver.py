"""RM-7.0 Knowledge Evolution Foundation — priority-chain resolver.

Resolves knowledge lookups by descending priority:
  USER -> RUNTIME -> LEARNING -> AUTO

USER entities are always preferred over runtime detections.
Locked entities cannot be overridden.
Aliases are expanded before entity lookup.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .models import (
    AliasEntry,
    EntityType,
    KnowledgeEntity,
    LearningCandidate,
    PriorityLevel,
    PRIORITY_ORDER,
)
from .store import KnowledgeStore


class KnowledgeResolver:
    """Resolve source terms to canonical forms using a priority chain.

    Usage::

        store = KnowledgeStore()
        resolver = KnowledgeResolver(store)
        entity = resolver.resolve("정태의")
        # -> KnowledgeEntity(source="정태의", canonical="鄭泰義", ...)
    """

    def __init__(self, store: KnowledgeStore):
        self._store = store
        self._entity_cache: Dict[str, Dict[str, KnowledgeEntity]] = {}
        self._alias_cache: Dict[str, Dict[str, AliasEntry]] = {}
        self._invalidated = True

    def invalidate(self) -> None:
        self._invalidated = True
        self._entity_cache.clear()
        self._alias_cache.clear()

    def _ensure_loaded(self) -> None:
        if not self._invalidated:
            return
        self._entity_cache.clear()
        self._alias_cache.clear()

        for priority in PRIORITY_ORDER:
            tier_key = priority.name.lower()
            ent_dict: Dict[str, KnowledgeEntity] = {}
            for kind in ("characters", "glossary"):
                for entity in self._store.load_entities(priority, kind):
                    existing = ent_dict.get(entity.source)
                    if existing is None or entity.confidence > existing.confidence:
                        ent_dict[entity.source] = entity
            self._entity_cache[tier_key] = ent_dict

            alias_list = self._store.load_aliases(priority)
            self._alias_cache[tier_key] = {a.alias: a for a in alias_list}

        self._invalidated = False

    def _resolve_alias(self, source: str) -> str:
        self._ensure_loaded()
        for tier_name in [p.name.lower() for p in PRIORITY_ORDER]:
            alias_entry = self._alias_cache.get(tier_name, {}).get(source)
            if alias_entry is not None:
                return alias_entry.target
        return source

    def resolve(self, source: str, entity_type: Optional[EntityType] = None) -> Optional[KnowledgeEntity]:
        """Resolve a source term to a KnowledgeEntity through the priority chain.

        Alias resolution is applied first; then the priority chain is searched.
        """
        resolved_source = self._resolve_alias(source)
        self._ensure_loaded()

        for priority in PRIORITY_ORDER:
            tier_key = priority.name.lower()
            entity = self._entity_cache.get(tier_key, {}).get(resolved_source)
            if entity is not None:
                if entity_type is not None and entity.entity_type != entity_type:
                    continue
                return entity

        return None

    def resolve_canonical(self, source: str, entity_type: Optional[EntityType] = None) -> str:
        """Return only the canonical string, falling back to source."""
        entity = self.resolve(source, entity_type)
        if entity is not None:
            return entity.canonical
        return source

    def resolve_with_priority(self, source: str) -> Optional[Tuple[KnowledgeEntity, PriorityLevel]]:
        """Return (entity, priority) for diagnostic purposes."""
        self._ensure_loaded()
        resolved = self._resolve_alias(source)

        for priority in PRIORITY_ORDER:
            tier_key = priority.name.lower()
            entity = self._entity_cache.get(tier_key, {}).get(resolved)
            if entity is not None:
                return entity, priority

        return None

    def find_candidate(self, source: str) -> Optional[LearningCandidate]:
        self._ensure_loaded()
        for candidate in self._store.load_candidates():
            if candidate.source == source:
                return candidate
        return None

    def list_all_canonicals(self) -> List[str]:
        self._ensure_loaded()
        seen: set = set()
        result: List[str] = []
        for priority in PRIORITY_ORDER:
            tier_key = priority.name.lower()
            for entity in self._entity_cache.get(tier_key, {}).values():
                if entity.canonical not in seen:
                    seen.add(entity.canonical)
                    result.append(entity.canonical)
        return result

    def source_priority(self, source: str) -> Optional[PriorityLevel]:
        self._ensure_loaded()
        resolved = self._resolve_alias(source)
        for priority in PRIORITY_ORDER:
            tier_key = priority.name.lower()
            if resolved in self._entity_cache.get(tier_key, {}):
                return priority
        return None