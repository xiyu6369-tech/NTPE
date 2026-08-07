"""RM-7.1 Entity Scanner — extract entity spans from translation output.

Given a knowledge payload (list of KnowledgeEntity dicts) and a
translated text, this scanner locates every canonical target form that
appears and returns EntityMatch records.

- Only reads; never mutates knowledge, glossaries, or translations.
- Matches via substring search in the translation text.
- Records position (character offset) for auditability.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.entity_consistency.models import (
    ENTITY_TYPE_TO_CATEGORY,
    REPORTABLE_TYPES,
    EntityMatch,
    EntityCategory,
)
from core.knowledge_evolution.models import EntityType


class EntityScanner:
    """Walk prepared knowledge entries against a translated document."""

    def __init__(self, knowledge_entries: Optional[List[Dict[str, Any]]] = None) -> None:
        self._entries: List[Dict[str, Any]] = list(knowledge_entries or [])

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def load(self, knowledge_entries: List[Dict[str, Any]]) -> None:
        self._entries = list(knowledge_entries)

    def scan(
        self,
        translated_text: str,
        entity_types: Optional[List[EntityType]] = None,
    ) -> List[EntityMatch]:
        matches: List[EntityMatch] = []
        seen: set = set()

        allowed = frozenset(entity_types) if entity_types else REPORTABLE_TYPES

        for entry in self._entries:
            entity_type_raw = str(entry.get("entity_type", ""))
            try:
                etype = EntityType(entity_type_raw)
            except ValueError:
                continue

            if etype not in allowed:
                continue

            canonical = str(entry.get("canonical", ""))
            if not canonical:
                continue

            source = str(entry.get("source", ""))

            pos = translated_text.find(canonical)
            if pos == -1:
                continue

            dedup_key = f"{etype.value}:{canonical}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            matches.append(EntityMatch(
                source=source,
                expected=canonical,
                found=canonical,
                entity_type=etype,
                position=pos,
            ))

        return matches

    def scan_all(self) -> Dict[str, Any]:
        return {
            "total_entries": self.entry_count,
            "entities_available": [e.get("canonical", "") for e in self._entries],
        }

    # ------------------------------------------------------------------
    # Utility: build index from TranslationOutput (dict-based pipeline)
    # ------------------------------------------------------------------

    @staticmethod
    def from_translation_output(payload: Dict[str, Any]) -> "EntityScanner":
        raw = payload.get("knowledge", payload.get("entities", []))
        if isinstance(raw, list):
            return EntityScanner(raw)
        return EntityScanner()

    @staticmethod
    def from_knowledge_entities(entities: List[Dict[str, Any]]) -> "EntityScanner":
        return EntityScanner(entities)