"""Foundation-07.1 Narrative Memory Engine."""

from __future__ import annotations

from typing import Dict, List, Optional

from .contracts import NarrativeMemoryEntry
from .memory_store import IntelligenceMemoryStore


class NarrativeMemoryEngine:
    """Stores and ranks narrative facts used by prompt/runtime layers."""

    def __init__(self, store: IntelligenceMemoryStore) -> None:
        self.store = store

    def remember(self, key: str, value: str, scope: str = "global", weight: int = 1) -> NarrativeMemoryEntry:
        return self.store.add_narrative(key=key, value=value, scope=scope, weight=weight)

    def get(self, key: str) -> Optional[NarrativeMemoryEntry]:
        return self.store._narrative.get(key)

    def ranked(self, scope: Optional[str] = None, limit: int = 20) -> List[Dict[str, object]]:
        entries = list(self.store._narrative.values())
        if scope is not None:
            entries = [entry for entry in entries if entry.scope == scope]
        entries.sort(key=lambda entry: entry.weight, reverse=True)
        return [entry.to_dict() for entry in entries[:limit]]

    def build_prompt_narrative(self, scope: Optional[str] = None, limit: int = 20) -> List[Dict[str, object]]:
        return self.ranked(scope=scope, limit=limit)
