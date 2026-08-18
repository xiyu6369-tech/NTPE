"""RM-6.2.0 Prompt Runtime builder.

Assembles structured prompt sections from MergedRuntime.
Does NOT generate actual prompts — only assembles sections in order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.knowledge_runtime.merger import MergedRuntime
from core.context_scene_memory.models import ContextSelectionResult, SceneMemoryRecord
from core.prompt_runtime.models import (
    SECTION_ORDER,
    SECTION_MAP,
    ChunkSection,
    PromptSection,
    SystemSection,
)
from core.prompt_runtime.sections import (
    SECTION_BUILDERS,
    build_chunk,
    build_entity_mapping,
    build_system,
    build_character,
    build_scene,
    build_narrative,
    build_context_selection,
)


@dataclass(frozen=True)
class PromptAssembly:
    """Result of prompt assembly — ordered sections ready for consumption."""

    sections: List[PromptSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "rm-6.2.0"

    @property
    def section_count(self) -> int:
        return len(self.sections)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sections": [s.to_dict() for s in self.sections],
            "metadata": dict(self.metadata),
            "version": self.version,
            "section_count": self.section_count,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "PromptAssembly":
        sections = [SECTION_MAP[s["name"]].from_dict(s) for s in payload.get("sections", [])]
        return cls(
            sections=sections,
            metadata=dict(payload.get("metadata") or {}),
            version=str(payload.get("version", "rm-6.2.0")),
        )


class PromptBuilder:
    """Builds PromptAssembly from MergedRuntime.

    Section order (fixed):
        System → Character → Entity Mapping → Glossary → Scene → Narrative → Style → Context → Chunk

    RM-8.2 Extensions (feature-gated via enable_cross_chunk_context):
        - context_selection: ContextSelectionResult for cross-chunk context
        - scene_state: SceneMemoryRecord for live scene state
        - narrative_state: dict from NarrativeIntelligenceEngine
        - character_memories: Selected character memories for prompt injection
        - enable_cross_chunk_context: Feature flag (default OFF for backward compatibility)
    """

    def __init__(
        self,
        chunk_text: str = "",
        system_metadata: Optional[Dict[str, Any]] = None,
        entity_injection_set: Optional[Any] = None,
        # RM-8.2 EXTENSIONS (feature-gated):
        context_selection: Optional[ContextSelectionResult] = None,
        scene_state: Optional[SceneMemoryRecord] = None,
        narrative_state: Optional[dict] = None,
        character_memories: Optional[Any] = None,
        enable_cross_chunk_context: bool = False,  # FEATURE FLAG — default OFF
    ):
        self._chunk_text = chunk_text
        self._system_metadata = system_metadata or {}
        self._entity_injection_set = entity_injection_set
        self._context_selection = context_selection
        self._scene_state = scene_state
        self._narrative_state = narrative_state
        self._character_memories = character_memories
        self._enable_cross_chunk_context = enable_cross_chunk_context

    def build(self, runtime: MergedRuntime) -> PromptAssembly:
        """Assemble all sections in fixed order from runtime."""
        sections: List[PromptSection] = []

        # System (always first)
        sections.append(build_system(runtime, self._system_metadata))

        # Character (parameterized with selected memories when enabled)
        sections.append(build_character(
            runtime,
            character_memories=self._character_memories
        ))

        # Entity Mapping (RM-7.2)
        sections.append(build_entity_mapping(runtime, self._entity_injection_set))

        # Domain sections (fixed order)
        for section_name in SECTION_ORDER[3:-1]:  # Skip System, Character, Entity Mapping, Chunk
            if section_name == "Scene":
                sections.append(build_scene(
                    runtime,
                    scene_state=self._scene_state if self._enable_cross_chunk_context else None
                ))
            elif section_name == "Narrative":
                sections.append(build_narrative(
                    runtime,
                    narrative_state=self._narrative_state if self._enable_cross_chunk_context else None
                ))
            elif section_name == "Context":  # NEW SECTION — only when enabled
                if self._enable_cross_chunk_context:
                    sections.append(build_context_selection(self._context_selection))
            else:
                builder = SECTION_BUILDERS[section_name]
                sections.append(builder(runtime))

        # Chunk (always last)
        sections.append(build_chunk(runtime, self._chunk_text))

        return PromptAssembly(
            sections=sections,
            metadata={
                "runtime_version": runtime.version,
                "runtime_domains": list(runtime.domains.keys()),
                "chunk_text_length": len(self._chunk_text),
                "has_entity_mapping": self._entity_injection_set is not None,
                "enable_cross_chunk_context": self._enable_cross_chunk_context,
            },
            version="rm-6.2.0",
        )

    def build_partial(
        self,
        runtime: MergedRuntime,
        include: Optional[List[str]] = None,
    ) -> PromptAssembly:
        """Build only specified sections (for testing/debugging)."""
        if include is None:
            include = list(SECTION_ORDER)

        sections: List[PromptSection] = []
        for section_name in SECTION_ORDER:
            if section_name not in include:
                continue
            if section_name == "System":
                sections.append(build_system(runtime, self._system_metadata))
            elif section_name == "Chunk":
                sections.append(build_chunk(runtime, self._chunk_text))
            elif section_name == "Entity Mapping":
                sections.append(build_entity_mapping(runtime, self._entity_injection_set))
            else:
                builder = SECTION_BUILDERS[section_name]
                sections.append(builder(runtime))

        return PromptAssembly(
            sections=sections,
            metadata={
                "runtime_version": runtime.version,
                "included_sections": include,
            },
            version="rm-6.2.0",
        )


def build_prompt(
    runtime: MergedRuntime,
    chunk_text: str = "",
    entity_injection_set: Optional[Any] = None,
) -> PromptAssembly:
    """Convenience function to build full prompt assembly.

    Args:
        runtime: MergedRuntime from knowledge_runtime
        chunk_text: Source text chunk to translate
        entity_injection_set: Optional EntityInjectionSet from entity_resolver (RM-7.2)

    Returns:
        PromptAssembly with all sections in fixed order
    """
    builder = PromptBuilder(chunk_text=chunk_text, entity_injection_set=entity_injection_set)
    return builder.build(runtime)


__all__ = [
    "PromptAssembly",
    "PromptBuilder",
    "build_prompt",
]