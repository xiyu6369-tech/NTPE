# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence
# =====================================================

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from .translation_memory_entry import TranslationMemoryEntry
from .translation_memory_events import MEMORY_COMPLETED, MEMORY_ENTRY_ADDED, MEMORY_MATCHED, MEMORY_STARTED, TranslationMemoryEventBus
from .translation_memory_exceptions import TranslationMemoryInputError
from .translation_memory_matcher import TranslationMemoryMatcher
from .translation_memory_policy import TranslationMemoryPolicy
from .translation_memory_result import TranslationMemoryResult
from .translation_memory_store import TranslationMemoryStore


class TranslationMemoryIntelligenceEngine:
    """Public Stage-16.5 facade for translation memory reuse."""

    stage = "Stage-16.5"
    name = "Translation Memory Intelligence"

    def __init__(self, *, store: TranslationMemoryStore | None = None, policy: TranslationMemoryPolicy | None = None, event_bus: TranslationMemoryEventBus | None = None) -> None:
        self.store = store or TranslationMemoryStore()
        self.policy = policy or TranslationMemoryPolicy()
        self.matcher = TranslationMemoryMatcher(self.policy)
        self.event_bus = event_bus or TranslationMemoryEventBus()

    def add_pair(self, source_text: str, target_text: str, **metadata: object) -> TranslationMemoryEntry:
        if not source_text or not source_text.strip():
            raise TranslationMemoryInputError("source_text must not be empty")
        if not target_text or not target_text.strip():
            raise TranslationMemoryInputError("target_text must not be empty")
        entry = TranslationMemoryEntry(
            source_text=source_text,
            target_text=target_text,
            source_language=str(metadata.get("source_language", "auto")),
            target_language=str(metadata.get("target_language", "zh-TW")),
            domain=str(metadata.get("domain", "general")),
            context_tags=list(metadata.get("context_tags", [])),
            terminology=dict(metadata.get("terminology", {})),
            character_refs=list(metadata.get("character_refs", [])),
            metadata=dict(metadata.get("metadata", {})),
        )
        self.store.add(entry)
        self.event_bus.emit(MEMORY_ENTRY_ADDED, entry_id=entry.entry_id, total_entries=len(self.store))
        return entry

    def find_matches(self, source_text: str, *, domain: str = "general", target_language: str = "zh-TW", context_tags: Sequence[str] | None = None, terminology: Mapping[str, str] | None = None, character_refs: Sequence[str] | None = None) -> TranslationMemoryResult:
        if not source_text or not source_text.strip():
            raise TranslationMemoryInputError("source_text must not be empty")
        self.event_bus.emit(MEMORY_STARTED, query_length=len(source_text), entry_count=len(self.store))
        matches = self.matcher.match(
            self.store,
            source_text,
            domain=domain,
            target_language=target_language,
            context_tags=context_tags or [],
            terminology=terminology or {},
            character_refs=character_refs or [],
        )
        result = TranslationMemoryResult(
            query=source_text,
            matches=matches,
            metrics={"entry_count": len(self.store), "match_count": len(matches), "best_score": matches[0].score if matches else 0.0},
        )
        self.event_bus.emit(MEMORY_MATCHED, match_count=len(matches), best_score=result.metrics["best_score"])
        self.event_bus.emit(MEMORY_COMPLETED, metrics=result.metrics)
        return result

    def export_memory(self, path: str | Path) -> None:
        self.store.export_json(path)

    def import_memory(self, path: str | Path) -> None:
        self.store = TranslationMemoryStore.import_json(path)
        self.matcher = TranslationMemoryMatcher(self.policy)

    def analyze(self, source_text: str) -> TranslationMemoryResult:
        return self.find_matches(source_text)
