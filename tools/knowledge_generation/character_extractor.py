"""
Character Extractor Agent (RM-5.7.2)

LLM-based character knowledge extraction from source text.
Extracts canonical names, aliases, roles, traits, relationships, and cultivation realms.
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
    CHARACTER_SCHEMA,
    ValidationPipeline,
    compile_character,
)


CHARACTER_EXTRACTION_PROMPT = """You are an expert literary analyst extracting character knowledge from {language} fiction text.

SOURCE TEXT:
{source_text}

EXTRACTION TASK:
Extract all characters mentioned in the source text. For each character, provide:
1. canonical_name - Official/canonical name
2. source_name - Name as it appears in source text
3. aliases - Alternative names, nicknames, titles
4. role - protagonist/antagonist/supporting/minor/narrator/unknown
5. traits - Personality traits, characteristics
6. relationships - Relationships to other characters (name -> relationship type)
7. cultivation_realm - Cultivation realm/power level (for xianxia/xuanhuan)
8. first_appearance - Chapter/volume reference
9. knowledge_tags - Domain-specific tags
10. arc_summary - Character arc/progression summary

OUTPUT FORMAT (JSON array):
[
  {
    "canonical_name": "...",
    "source_name": "...",
    "aliases": ["..."],
    "role": "protagonist|antagonist|supporting|minor|narrator|unknown",
    "traits": ["..."],
    "relationships": {{"character_name": "relationship_type"}},
    "cultivation_realm": "...",
    "first_appearance": "...",
    "knowledge_tags": ["..."],
    "arc_summary": "..."
  }
]

Only include characters with clear textual evidence. Use "unknown" for uncertain fields.
"""


class CharacterExtractor(BaseKnowledgeExtractor):
    """LLM-based character knowledge extractor."""

    def __init__(self, config: ExtractorConfig = None):
        if config is None:
            config = ExtractorConfig(
                domain="character",
                strategy=ExtractionStrategy.CHUNK_BY_CHUNK,
                chunk_size=3000,
                chunk_overlap=300,
                max_entities_per_chunk=20,
                confidence_threshold=0.4,
            )
        super().__init__(config)
        self._prompt_template = CHARACTER_EXTRACTION_PROMPT

    @property
    def schema(self):
        return CHARACTER_SCHEMA

    @property
    def default_prompt(self) -> str:
        return CHARACTER_EXTRACTION_PROMPT

    def _extract_chunk(self, context: ExtractionContext) -> ExtractionResult:
        """Extract characters from a single chunk of text."""
        # This is a scaffold - actual LLM integration would go here
        # For now, return empty result with proper structure
        return ExtractionResult.success_result(
            entities=[],
            extraction_time_ms=0.0,
            metadata={
                "extractor": "CharacterExtractor",
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

                entity = KnowledgeEntity(
                    entity_id=str(uuid.uuid4()),
                    entity_type=EntityType.CHARACTER,
                    name=item.get("canonical_name", item.get("source_name", "")),
                    attributes={
                        "canonical_name": item.get("canonical_name", ""),
                        "source_name": item.get("source_name", ""),
                        "aliases": item.get("aliases", []),
                        "role": item.get("role", "unknown"),
                        "traits": item.get("traits", []),
                        "relationships": item.get("relationships", {}),
                        "cultivation_realm": item.get("cultivation_realm", ""),
                        "first_appearance": item.get("first_appearance", ""),
                        "knowledge_tags": item.get("knowledge_tags", []),
                        "arc_summary": item.get("arc_summary", ""),
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


def create_character_extractor(config: ExtractorConfig = None) -> CharacterExtractor:
    """Factory function to create a CharacterExtractor."""
    return CharacterExtractor(config)