"""Foundation-07.1 Translation Intelligence Engine.

The engine is an additive orchestration layer above Foundation-07.0 contracts.
It exposes one stable facade that Runtime, Prompt Pipeline, or future adapters can
use without binding to internal memory implementation details.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .adapter import IntelligenceAdapter
from .character_engine import CharacterMemoryEngine
from .consistency_engine import ConsistencyEngine
from .glossary_engine import GlossaryIntelligenceEngine
from .memory_store import IntelligenceMemoryStore
from .narrative_engine import NarrativeMemoryEngine
from .scene_engine import SceneMemoryEngine


class TranslationIntelligenceEngine:
    """Main orchestration engine for translation intelligence."""

    version = "foundation-07.1"

    def __init__(self, store: Optional[IntelligenceMemoryStore] = None) -> None:
        self.store = store or IntelligenceMemoryStore()
        self.characters = CharacterMemoryEngine(self.store)
        self.glossary = GlossaryIntelligenceEngine(self.store)
        self.narrative = NarrativeMemoryEngine(self.store)
        self.scenes = SceneMemoryEngine(self.store)
        self.consistency = ConsistencyEngine(self.store)
        self.adapter = IntelligenceAdapter(self.store)

    def build_snapshot(self) -> Dict[str, Any]:
        snapshot = self.store.build_snapshot().to_dict()
        manifest = dict(snapshot.get("manifest", {}))
        manifest.update(
            {
                "component": "translation_intelligence_engine",
                "foundation": "07.1",
                "engine_version": self.version,
            }
        )
        snapshot["manifest"] = manifest
        return snapshot

    def build_prompt_context(self, source_text: str = "") -> Dict[str, Any]:
        return {
            "type": "translation_intelligence_engine_context",
            "version": self.version,
            "characters": self.characters.extract_mentions(source_text)
            if source_text
            else self.characters.build_prompt_memory(),
            "glossary": self.glossary.match_terms(source_text)
            if source_text
            else self.glossary.build_prompt_glossary(),
            "narrative": self.narrative.build_prompt_narrative(),
            "scenes": self.scenes.build_prompt_scenes(),
        }

    def build_runtime_manifest_component(self) -> Dict[str, Any]:
        snapshot = self.build_snapshot()
        return {
            "name": "translation_intelligence_engine",
            "version": self.version,
            "enabled": True,
            "manifest": snapshot["manifest"],
        }

    def attach_to_manifest(self, manifest: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        next_manifest: Dict[str, Any] = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append(self.build_runtime_manifest_component())
        next_manifest["components"] = components
        return next_manifest

    def attach_to_prompt_package(self, prompt_package: Optional[Dict[str, Any]], source_text: str = "") -> Dict[str, Any]:
        next_package: Dict[str, Any] = dict(prompt_package or {})
        context_components = list(next_package.get("context_components", []))
        context_components.append(self.build_prompt_context(source_text=source_text))
        next_package["context_components"] = context_components
        return next_package

    def process_segment(
        self,
        source_text: str,
        output_text: str = "",
        segment_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "segment_id": segment_id,
            "metadata": dict(metadata or {}),
            "prompt_context": self.build_prompt_context(source_text),
            "snapshot": self.build_snapshot(),
        }
        if output_text:
            result["consistency"] = self.consistency.validate_translation(source_text, output_text)
        return result
