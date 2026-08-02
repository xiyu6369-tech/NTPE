"""
Narrative Extractor Agent (RM-5.7.2)

LLM-based narrative knowledge extraction (plot points, timelines, world rules, character milestones).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
import uuid
from datetime import datetime, timezone

from core.knowledge_generation import (
    BaseKnowledgeExtractor,
    ExtractorConfig,
    ExtractionContext,
    ExtractionResult,
    ExtractionStrategy,
    KnowledgeEntity,
    EntityType,
    NARRATIVE_SCHEMA,
    ValidationPipeline,
    compile_narrative,
)


NARRATIVE_EXTRACTION_PROMPT = """You are an expert literary analyst extracting narrative knowledge from {language} fiction text.

SOURCE TEXT:
{source_text}

EXTRACTION TASK:
Extract narrative structure elements from the source text. Four types:

1. PLOT POINTS - Key narrative events
   - plot_id: PP-001 format
   - title: Brief title
   - type: inciting/rising/climax/falling/resolution/revelation/twist/setup
   - description: Detailed description
   - affected_characters: List of character IDs
   - prerequisite_plots: Prior plot IDs
   - consequence_plots: Following plot IDs
   - timeline_position: Numeric position

2. TIMELINES - Chronological event sequences
   - timeline_id: TL-001 format
   - name: Timeline name
   - events: Array of {position, event_id, event_type, description}

3. WORLD RULES - Setting rules and systems
   - rule_id: WR-001 format
   - category: cultivation_system/magic_system/political_structure/geography/history/technology/social_custom
   - name: Rule name
   - description: Detailed description
   - constraints: List of constraints
   - exceptions: List of exceptions
   - source_volume: Volume number

4. CHARACTER MILESTONES - Key character development points
   - character_id: Character reference
   - milestone_type: breakthrough/relationship/revelation/loss/achievement/transformation
   - description: Description
   - chapter: Chapter number
   - impact_level: 1-10

OUTPUT FORMAT (JSON array):
[
  {"narrative_type": "plot_point", "plot_point": {...}},
  {"narrative_type": "timeline", "timeline": {...}},
  {"narrative_type": "world_rule", "world_rule": {...}},
  {"narrative_type": "character_milestone", "character_milestone": {...}}
]

Only include elements with clear textual evidence.
"""


class NarrativeExtractor(BaseKnowledgeExtractor):
    """LLM-based narrative knowledge extractor (plot, timeline, world rules, milestones)."""

    def __init__(self, config: ExtractorConfig = None):
        if config is None:
            config = ExtractorConfig(
                domain="narrative",
                strategy=ExtractionStrategy.WHOLE_DOCUMENT,
                chunk_size=8000,
                chunk_overlap=500,
                max_entities_per_chunk=15,
                confidence_threshold=0.35,
            )
        super().__init__(config)
        self._prompt_template = NARRATIVE_EXTRACTION_PROMPT

    @property
    def schema(self):
        return NARRATIVE_SCHEMA

    @property
    def default_prompt(self) -> str:
        return NARRATIVE_EXTRACTION_PROMPT

    def _extract_chunk(self, context: ExtractionContext) -> ExtractionResult:
        """Extract narrative elements from a chunk/document."""
        return ExtractionResult.success_result(
            entities=[],
            extraction_time_ms=0.0,
            metadata={
                "extractor": "NarrativeExtractor",
                "chunk_index": context.chunk_index,
                "note": "Scaffold implementation - LLM integration pending"
            }
        )

    def _parse_llm_response(self, response: str, context: ExtractionContext) -> List[KnowledgeEntity]:
        """Parse LLM JSON response into KnowledgeEntity objects."""
        entities = []
        try:
            data = json.loads(response)
            if not isinstance(data, list):
                return entities

            for item in data:
                if not isinstance(item, dict):
                    continue

                narrative_type = item.get("narrative_type", "plot_point")
                
                if narrative_type == "plot_point":
                    attrs = item.get("plot_point", {})
                    name = attrs.get("plot_id", "")
                elif narrative_type == "timeline":
                    attrs = item.get("timeline", {})
                    name = attrs.get("timeline_id", "")
                elif narrative_type == "world_rule":
                    attrs = item.get("world_rule", {})
                    name = attrs.get("rule_id", "")
                elif narrative_type == "character_milestone":
                    attrs = item.get("character_milestone", {})
                    name = f"milestone_{attrs.get('character_id', 'unknown')}"
                else:
                    attrs = {}
                    name = ""

                entity = KnowledgeEntity(
                    entity_id=str(uuid.uuid4()),
                    entity_type=EntityType.NARRATIVE,
                    name=name,
                    attributes={
                        "narrative_type": narrative_type,
                        **attrs
                    },
                    source_text=context.source_text[:500],
                    source_location=context.source_location,
                    confidence=item.get("confidence", 0.5),
                    metadata={
                        "extraction_method": "llm",
                        "extraction_model": self.config.metadata.get("model", "unknown"),
                        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                entities.append(entity)

        except json.JSONDecodeError:
            pass

        return entities


def create_narrative_extractor(config: ExtractorConfig = None) -> NarrativeExtractor:
    """Factory function to create a NarrativeExtractor."""
    return NarrativeExtractor(config)