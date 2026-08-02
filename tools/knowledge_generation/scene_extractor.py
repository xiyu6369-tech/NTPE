"""
Scene Extractor Agent (RM-5.7.2)

LLM-based scene boundary detection and attribute extraction from source text.
Extracts scenes with location, time, participants, plot points, tone, etc.
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
    SCENE_SCHEMA,
    ValidationPipeline,
    compile_scene,
)


SCENE_EXTRACTION_PROMPT = """You are an expert literary analyst extracting scene knowledge from {language} fiction text.

SOURCE TEXT:
{source_text}

EXTRACTION TASK:
Identify scene boundaries and extract scene attributes. For each scene, provide:
1. scene_id - Structured ID (SC-001, SC-002, etc.)
2. title - Descriptive title
3. volume - Volume number
4. chapter_range - Chapter range (e.g., "1-3" or "5")
5. location - Primary location
6. time_of_day - dawn/morning/noon/afternoon/evening/night/midnight/unknown
7. participants - Characters present with status (present/mentioned/absent/exited) and role
8. plot_points - Related plot point IDs
9. summary - Brief scene summary
10. tone - tense/restrained/heated/atmospheric/neutral/melancholic/joyful/ominous/other
11. unresolved_references - Unresolved references needing resolution
12. boundary_type - same_scene/scene_transition/chapter_transition/volume_transition/time_skip/perspective_shift

OUTPUT FORMAT (JSON array):
[
  {
    "scene_id": "SC-001",
    "title": "...",
    "volume": 1,
    "chapter_range": "1",
    "location": "...",
    "time_of_day": "morning",
    "participants": [
      {{"character_id": "...", "status": "present", "role": "protagonist"}}
    ],
    "plot_points": ["PP-001"],
    "summary": "...",
    "tone": "neutral",
    "unresolved_references": [
      {{"surface_form": "...", "reference_type": "...", "candidate_targets": ["..."], "resolution_status": "unresolved"}}
    ],
    "boundary_type": "scene_transition"
  }
]

Only include scenes with clear textual boundaries. Use "unknown" for uncertain fields.
"""


class SceneExtractor(BaseKnowledgeExtractor):
    """LLM-based scene boundary detection and attribute extractor."""

    def __init__(self, config: ExtractorConfig = None):
        if config is None:
            config = ExtractorConfig(
                domain="scene",
                strategy=ExtractionStrategy.CHUNK_BY_CHUNK,
                chunk_size=4000,
                chunk_overlap=400,
                max_entities_per_chunk=10,
                confidence_threshold=0.4,
            )
        super().__init__(config)
        self._prompt_template = SCENE_EXTRACTION_PROMPT

    @property
    def schema(self):
        return SCENE_SCHEMA

    @property
    def default_prompt(self) -> str:
        return SCENE_EXTRACTION_PROMPT

    def _extract_chunk(self, context: ExtractionContext) -> ExtractionResult:
        """Extract scenes from a single chunk of text."""
        return ExtractionResult.success_result(
            entities=[],
            extraction_time_ms=0.0,
            metadata={
                "extractor": "SceneExtractor",
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
                    entity_type=EntityType.SCENE,
                    name=item.get("scene_id", ""),
                    attributes={
                        "scene_id": item.get("scene_id", ""),
                        "title": item.get("title", ""),
                        "volume": item.get("volume", 1),
                        "chapter_range": item.get("chapter_range", ""),
                        "location": item.get("location", ""),
                        "time_of_day": item.get("time_of_day", "unknown"),
                        "participants": item.get("participants", []),
                        "plot_points": item.get("plot_points", []),
                        "summary": item.get("summary", ""),
                        "tone": item.get("tone", "neutral"),
                        "unresolved_references": item.get("unresolved_references", []),
                        "boundary_type": item.get("boundary_type", "scene_transition"),
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


def create_scene_extractor(config: ExtractorConfig = None) -> SceneExtractor:
    """Factory function to create a SceneExtractor."""
    return SceneExtractor(config)