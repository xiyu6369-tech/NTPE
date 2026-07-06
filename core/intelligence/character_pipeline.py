# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

from __future__ import annotations

from typing import Iterable, List

from .character_graph import CharacterGraph
from .character_metrics import build_character_metrics
from .character_pronoun import resolve_pronouns
from .character_registry import CharacterRegistry
from .character_result import CharacterFinding, CharacterIntelligenceResult, CharacterMention


class CharacterPipeline:
    """Deterministic character relationship analysis pipeline."""

    def __init__(self, registry: CharacterRegistry | None = None, graph: CharacterGraph | None = None) -> None:
        self.registry = registry or CharacterRegistry()
        self.graph = graph or CharacterGraph()

    def run(self, texts: Iterable[str], *, segment_prefix: str = "char") -> CharacterIntelligenceResult:
        materialized = [text for text in texts if text and text.strip()]
        mentions: List[CharacterMention] = []
        findings: List[CharacterFinding] = []
        recent: List[str] = []
        pronouns = {}
        counter = 0

        for index, text in enumerate(materialized, start=1):
            segment_id = f"{segment_prefix}_{index}"
            for record in self.registry.all():
                matched_names = [name for name in record.names() if name and name in text]
                if not matched_names:
                    continue
                counter += 1
                canonical = record.canonical_name
                recent.append(canonical)
                self.graph.add_character(canonical)
                mentions.append(CharacterMention(
                    mention_id=f"mention_{counter}",
                    name=matched_names[0],
                    canonical_name=canonical,
                    segment_id=segment_id,
                    mention_type="alias" if matched_names[0] != canonical else "name",
                ))
                if len(set(matched_names)) > 1:
                    findings.append(CharacterFinding(
                        category="alias",
                        severity="warning",
                        message="Multiple aliases for the same character appeared in one segment.",
                        character=canonical,
                        segment_id=segment_id,
                    ))
            pronouns.update(resolve_pronouns(text, recent))

        result = CharacterIntelligenceResult(
            mentions=mentions,
            characters=self.registry.to_dict(),
            relationships=[edge.to_dict() for edge in self.graph.relationships()],
            pronoun_candidates=pronouns,
            findings=findings,
        )
        result.metrics = build_character_metrics(result)
        return result
