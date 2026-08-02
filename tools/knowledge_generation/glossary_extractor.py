"""
Glossary Extractor Agent (RM-5.7.2)

LLM-based glossary/terminology knowledge extraction from source text.
Extracts terms with canonical translations, domain tags, POS, context rules, etc.
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
    GLOSSARY_SCHEMA,
    ValidationPipeline,
    compile_glossary,
)


GLOSSARY_EXTRACTION_PROMPT = """You are an expert terminologist extracting glossary knowledge from {language} fiction text.

SOURCE TEXT:
{source_text}

EXTRACTION TASK:
Extract all important terms, phrases, and terminology from the source text. For each term, provide:
1. canonical_translation - Official/canonical translation
2. source_term - Original term in source language
3. domain_tags - Domain classifications (cultivation, medicine, weapon, location, organization, title, honorific, technique, artifact, creature, concept, other)
4. part_of_speech - noun/verb/adjective/adverb/proper_noun/phrase/idiom/other
5. context_rules - Context-dependent translation rules (context -> translation)
4. forbidden_forms - Translations that should never be used
5. aliases - Alternative forms of the source term
6. notes - Additional notes or usage guidance
6. relationships - Semantic relationships (synonyms, antonyms, hypernyms, hyponyms)

OUTPUT FORMAT (JSON array):
[
  {
    "canonical_translation": "...",
    "source_term": "...",
    "domain_tags": ["cultivation", "technique"],
    "part_of_speech": "noun|verb|adjective|adverb|proper_noun|phrase|idiom|other",
    "context_rules": {{"context": "translation"}},
    "forbidden_forms": ["..."],
    "aliases": ["..."],
    "notes": "...",
    "relationships": {{"synonyms": ["..."], "antonyms": ["..."], "hypernyms": ["..."], "hyponyms": ["..."]}}
  }
]

Only include terms with clear textual evidence. Focus on domain-specific terminology.
"""


class GlossaryExtractor(BaseKnowledgeExtractor):
    """LLM-based glossary/terminology knowledge extractor."""

    def __init__(self, config: ExtractorConfig = None):
        if config is None:
            config = ExtractorConfig(
                domain="glossary",
                strategy=ExtractionStrategy.CHUNK_BY_CHUNK,
                chunk_size=3000,
                chunk_overlap=300,
                max_entities_per_chunk=30,
                confidence_threshold=0.4,
            )
        super().__init__(config)
        self._prompt_template = GLOSSARY_EXTRACTION_PROMPT

    @property
    def schema(self):
        return GLOSSARY_SCHEMA

    @property
    def default_prompt(self) -> str:
        return GLOSSARY_EXTRACTION_PROMPT

    def _extract_chunk(self, context: ExtractionContext) -> ExtractionResult:
        """Extract glossary terms from a single chunk of text."""
        return ExtractionResult.success_result(
            entities=[],
            extraction_time_ms=0.0,
            metadata={
                "extractor": "GlossaryExtractor",
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
                    entity_type=EntityType.GLOSSARY,
                    name=item.get("source_term", ""),
                    attributes={
                        "canonical_translation": item.get("canonical_translation", ""),
                        "source_term": item.get("source_term", ""),
                        "domain_tags": item.get("domain_tags", []),
                        "part_of_speech": item.get("part_of_speech", "noun"),
                        "context_rules": item.get("context_rules", {}),
                        "forbidden_forms": item.get("forbidden_forms", []),
                        "aliases": item.get("aliases", []),
                        "notes": item.get("notes", ""),
                        "relationships": item.get("relationships", {}),
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


def create_glossary_extractor(config: ExtractorConfig = None) -> GlossaryExtractor:
    """Factory function to create a GlossaryExtractor."""
    return GlossaryExtractor(config)