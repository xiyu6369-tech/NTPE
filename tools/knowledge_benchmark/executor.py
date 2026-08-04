"""
Extraction Executor (RM-5.8.3)

Executes knowledge extractors against benchmark source texts.
Returns extraction results as plain dictionaries (no Runtime dependency).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import time

from core.knowledge_generation.models import ExtractionContext

from tools.knowledge_generation import (
    create_character_extractor,
    create_glossary_extractor,
    create_scene_extractor,
    create_narrative_extractor,
    create_style_extractor,
)


EXTRACTOR_FACTORIES: Dict[str, Callable] = {
    "character": create_character_extractor,
    "glossary": create_glossary_extractor,
    "scene": create_scene_extractor,
    "narrative": create_narrative_extractor,
    "style": create_style_extractor,
}


EXTRACTOR_DISPLAY_NAMES: Dict[str, str] = {
    "character": "Character Extractor",
    "glossary": "Glossary Extractor",
    "scene": "Scene Extractor",
    "narrative": "Narrative Extractor",
    "style": "Style Extractor",
}


@dataclass
class ExecutionResult:
    extractor_name: str
    source_text: str
    extracted_entities: List[Dict[str, Any]]
    elapsed_ms: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExtractionExecutor:
    """Executes knowledge extractors against benchmark source texts."""

    def __init__(self):
        self._extractors: Dict[str, Any] = {}

    def execute(self, extractor_name: str, source_text: str) -> ExecutionResult:
        factory = EXTRACTOR_FACTORIES.get(extractor_name)
        if factory is None:
            raise ValueError(f"Unknown extractor: {extractor_name}")

        try:
            ext = factory()
        except Exception as e:
            return ExecutionResult(
                extractor_name=extractor_name,
                source_text=source_text,
                extracted_entities=[],
                elapsed_ms=0.0,
                error=f"Failed to create extractor: {e}",
            )

        context = ExtractionContext(
            document_id="benchmark",
            document_title="Benchmark Text",
            chunk_text=source_text,
            chunk_index=0,
            chunk_start=0,
            chunk_end=len(source_text),
        )

        start = time.perf_counter()
        try:
            result = ext.extract(context)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            entities = self._to_dict_list(result)
            return ExecutionResult(
                extractor_name=extractor_name,
                source_text=source_text,
                extracted_entities=entities,
                elapsed_ms=round(elapsed_ms, 2),
                metadata={
                    "extraction_method": "offline",
                    "note": "Scaffold extraction - LLM integration pending",
                },
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return ExecutionResult(
                extractor_name=extractor_name,
                source_text=source_text,
                extracted_entities=[],
                elapsed_ms=round(elapsed_ms, 2),
                error=str(e),
            )

    @staticmethod
    def _to_dict_list(result: Any) -> List[Dict[str, Any]]:
        entities = []
        try:
            if hasattr(result, 'entities'):
                raw = result.entities
            elif isinstance(result, dict):
                raw = result.get("entities", [])
            elif isinstance(result, list):
                raw = result
            else:
                raw = []

            for entity in raw:
                if hasattr(entity, 'to_dict'):
                    d = entity.to_dict()
                elif isinstance(entity, dict):
                    d = entity
                else:
                    continue
                entities.append(d)
        except Exception:
            pass
        return entities