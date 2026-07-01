"""Foundation-07.1 Glossary Intelligence Engine."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional

from .contracts import GlossaryEntry
from .memory_store import IntelligenceMemoryStore


class GlossaryIntelligenceEngine:
    """Glossary lookup, matching, and prompt export service."""

    def __init__(self, store: IntelligenceMemoryStore) -> None:
        self.store = store

    def remember(
        self,
        source_term: str,
        target_term: str,
        category: str = "general",
        locked: bool = True,
        notes: str = "",
    ) -> GlossaryEntry:
        return self.store.add_glossary(
            source_term=source_term,
            target_term=target_term,
            category=category,
            locked=locked,
            notes=notes,
        )

    def resolve(self, source_term: str, fuzzy: bool = True, threshold: float = 0.84) -> Optional[GlossaryEntry]:
        direct = self.store.get_glossary(source_term)
        if direct is not None or not fuzzy:
            return direct

        best_entry: Optional[GlossaryEntry] = None
        best_score = 0.0
        for entry in self.store._glossary.values():
            score = SequenceMatcher(None, source_term, entry.source_term).ratio()
            if score > best_score:
                best_score = score
                best_entry = entry
        if best_score >= threshold:
            return best_entry
        return None

    def match_terms(self, text: str, locked_only: bool = False) -> List[Dict[str, object]]:
        matches: List[Dict[str, object]] = []
        for entry in self.store._glossary.values():
            if locked_only and not entry.locked:
                continue
            if entry.source_term in text or entry.target_term in text:
                matches.append(entry.to_dict())
        return matches

    def build_prompt_glossary(self, limit: int = 50, locked_only: bool = False) -> List[Dict[str, object]]:
        items: Iterable[GlossaryEntry] = self.store._glossary.values()
        if locked_only:
            items = [entry for entry in items if entry.locked]
        return [entry.to_dict() for entry in list(items)[:limit]]
