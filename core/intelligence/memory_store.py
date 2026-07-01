"""In-memory intelligence store for Foundation-07.0.

The store is deliberately simple and serializable so future Foundation versions can
replace persistence without breaking adapter callers.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .contracts import (
    CharacterMemoryEntry,
    GlossaryEntry,
    IntelligenceSnapshot,
    NarrativeMemoryEntry,
    SceneMemoryEntry,
)


class IntelligenceMemoryStore:
    """Canonical storage facade for translation intelligence data."""

    def __init__(self) -> None:
        self._characters: Dict[str, CharacterMemoryEntry] = {}
        self._glossary: Dict[str, GlossaryEntry] = {}
        self._narrative: Dict[str, NarrativeMemoryEntry] = {}
        self._scenes: Dict[str, SceneMemoryEntry] = {}

    def add_character(
        self,
        source_name: str,
        target_name: str,
        aliases: Optional[Iterable[str]] = None,
        traits: Optional[Iterable[str]] = None,
        notes: str = "",
    ) -> CharacterMemoryEntry:
        entry = CharacterMemoryEntry(
            source_name=source_name,
            target_name=target_name,
            aliases=list(aliases or []),
            traits=list(traits or []),
            notes=notes,
        )
        self._characters[source_name] = entry
        return entry

    def get_character(self, source_name: str) -> Optional[CharacterMemoryEntry]:
        return self._characters.get(source_name)

    def add_glossary(
        self,
        source_term: str,
        target_term: str,
        category: str = "general",
        locked: bool = True,
        notes: str = "",
    ) -> GlossaryEntry:
        entry = GlossaryEntry(
            source_term=source_term,
            target_term=target_term,
            category=category,
            locked=locked,
            notes=notes,
        )
        self._glossary[source_term] = entry
        return entry

    def get_glossary(self, source_term: str) -> Optional[GlossaryEntry]:
        return self._glossary.get(source_term)

    def add_narrative(self, key: str, value: str, scope: str = "global", weight: int = 1) -> NarrativeMemoryEntry:
        entry = NarrativeMemoryEntry(key=key, value=value, scope=scope, weight=weight)
        self._narrative[key] = entry
        return entry

    def add_scene(
        self,
        scene_id: str,
        summary: str,
        location: str = "",
        timeline: str = "",
        participants: Optional[Iterable[str]] = None,
    ) -> SceneMemoryEntry:
        entry = SceneMemoryEntry(
            scene_id=scene_id,
            summary=summary,
            location=location,
            timeline=timeline,
            participants=list(participants or []),
        )
        self._scenes[scene_id] = entry
        return entry

    def build_snapshot(self) -> IntelligenceSnapshot:
        return IntelligenceSnapshot(
            characters=[entry.to_dict() for entry in self._characters.values()],
            glossary=[entry.to_dict() for entry in self._glossary.values()],
            narrative=[entry.to_dict() for entry in self._narrative.values()],
            scenes=[entry.to_dict() for entry in self._scenes.values()],
            manifest={
                "component": "translation_intelligence_contract",
                "foundation": "07.0",
                "character_count": len(self._characters),
                "glossary_count": len(self._glossary),
                "narrative_count": len(self._narrative),
                "scene_count": len(self._scenes),
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.build_snapshot().to_dict()
