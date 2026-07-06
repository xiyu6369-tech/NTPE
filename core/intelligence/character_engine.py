# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

from __future__ import annotations

from typing import Iterable, Sequence

from .character_events import CHARACTER_ANALYZED, CHARACTER_COMPLETED, CHARACTER_STARTED, CharacterEventBus
from .character_exceptions import CharacterInputError
from .character_graph import CharacterGraph
from .character_memory import CharacterMemory
from .character_pipeline import CharacterPipeline
from .character_registry import CharacterRegistry
from .character_result import CharacterIntelligenceResult


class CharacterRelationshipIntelligenceEngine:
    """Public Stage-16.3 facade for character relationship intelligence."""

    stage = "Stage-16.3"
    name = "Character Relationship Intelligence Engine"

    def __init__(self, *, registry: CharacterRegistry | None = None, graph: CharacterGraph | None = None, event_bus: CharacterEventBus | None = None) -> None:
        self.registry = registry or CharacterRegistry()
        self.graph = graph or CharacterGraph()
        self.memory = CharacterMemory()
        self.event_bus = event_bus or CharacterEventBus()
        self.pipeline = CharacterPipeline(self.registry, self.graph)

    def register_character(self, canonical_name: str, **kwargs: object):
        if not canonical_name or not canonical_name.strip():
            raise CharacterInputError("Character canonical name must not be empty.")
        return self.registry.register(canonical_name.strip(), **kwargs)

    def add_relationship(self, source: str, target: str, relation_type: str = "unknown", **metadata: object):
        if not source or not target:
            raise CharacterInputError("Relationship source and target must not be empty.")
        return self.graph.add_relationship(source, target, relation_type, **metadata)

    def analyze_texts(self, texts: Sequence[str], *, source: str = "runtime") -> CharacterIntelligenceResult:
        materialized = [text for text in texts if text and text.strip()]
        if not materialized:
            raise CharacterInputError("Character analysis text must not be empty.")
        self.event_bus.emit(CHARACTER_STARTED, segment_count=len(materialized), source=source)
        result = self.pipeline.run(materialized, segment_prefix=source)
        self.memory.observe(mention.canonical_name for mention in result.mentions)
        self.event_bus.emit(CHARACTER_ANALYZED, character_count=result.character_count, mention_count=result.mention_count)
        self.event_bus.emit(CHARACTER_COMPLETED, finding_count=len(result.findings))
        return result

    def analyze_text(self, text: str, *, source: str = "runtime") -> CharacterIntelligenceResult:
        return self.analyze_texts([text], source=source)

    def analyze(self, texts: Iterable[str]) -> CharacterIntelligenceResult:
        return self.analyze_texts(list(texts))
