"""Foundation-07.1 Character Memory Engine.

This engine builds on the Foundation-07.0 contract/store layer without changing
existing store semantics. It provides a stable, runtime-safe facade for learning,
resolving, and exporting character memory.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .contracts import CharacterMemoryEntry
from .memory_store import IntelligenceMemoryStore


class CharacterMemoryEngine:
    """High-level character memory service."""

    def __init__(self, store: IntelligenceMemoryStore) -> None:
        self.store = store

    def remember(
        self,
        source_name: str,
        target_name: str,
        aliases: Optional[Iterable[str]] = None,
        traits: Optional[Iterable[str]] = None,
        notes: str = "",
    ) -> CharacterMemoryEntry:
        return self.store.add_character(
            source_name=source_name,
            target_name=target_name,
            aliases=aliases,
            traits=traits,
            notes=notes,
        )

    def resolve(self, name: str) -> Optional[CharacterMemoryEntry]:
        direct = self.store.get_character(name)
        if direct is not None:
            return direct

        for entry in self.store._characters.values():  # compatibility read
            if name == entry.target_name or name in entry.aliases:
                return entry
        return None

    def extract_mentions(self, text: str) -> List[Dict[str, str]]:
        mentions: List[Dict[str, str]] = []
        for entry in self.store._characters.values():
            candidates = [entry.source_name, entry.target_name, *entry.aliases]
            if any(candidate and candidate in text for candidate in candidates):
                mentions.append(
                    {
                        "source_name": entry.source_name,
                        "target_name": entry.target_name,
                    }
                )
        return mentions

    def build_prompt_memory(self, limit: int = 20) -> List[Dict[str, object]]:
        entries = list(self.store._characters.values())[:limit]
        return [entry.to_dict() for entry in entries]
