"""RM-6.2.0 Prompt Runtime — Prompt Assembly Layer.

Consumes MergedRuntime from knowledge_runtime and produces structured PromptAssembly.
Does not modify Translation Engine. No provider imports. No network calls.
"""

from __future__ import annotations

from core.prompt_runtime.models import (
    PromptSection,
    CharacterSection,
    GlossarySection,
    SceneSection,
    NarrativeSection,
    StyleSection,
    SystemSection,
    ChunkSection,
    SECTION_ORDER,
    SECTION_MAP,
)
from core.prompt_runtime.sections import (
    build_system,
    build_character,
    build_glossary,
    build_scene,
    build_narrative,
    build_style,
    build_chunk,
    SECTION_BUILDERS,
)
from core.prompt_runtime.builder import (
    PromptAssembly,
    PromptBuilder,
    build_prompt,
)

__all__ = [
    # Models
    "PromptSection",
    "CharacterSection",
    "GlossarySection",
    "SceneSection",
    "NarrativeSection",
    "StyleSection",
    "SystemSection",
    "ChunkSection",
    "SECTION_ORDER",
    "SECTION_MAP",
    # Sections
    "build_system",
    "build_character",
    "build_glossary",
    "build_scene",
    "build_narrative",
    "build_style",
    "build_chunk",
    "SECTION_BUILDERS",
    # Builder
    "PromptAssembly",
    "PromptBuilder",
    "build_prompt",
]