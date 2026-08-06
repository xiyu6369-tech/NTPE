"""RM-6.2.0 Prompt Runtime section builders.

Each domain has an independent builder function that transforms
MergedRuntime domain data into structured PromptSection objects.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.knowledge_runtime.merger import MergedRuntime
from core.prompt_runtime.models import (
    CharacterSection,
    ChunkSection,
    GlossarySection,
    NarrativeSection,
    SceneSection,
    StyleSection,
    SystemSection,
)


def _entries_to_content(entries: Dict[str, Any], template: str = "{key}: {value}") -> str:
    """Convert domain entries to formatted content string."""
    if not entries:
        return ""
    lines = []
    for key, value in entries.items():
        lines.append(template.format(key=key, value=value))
    return "\n".join(lines)


def build_system(runtime: MergedRuntime, metadata: Optional[Dict[str, Any]] = None) -> SystemSection:
    """Build System section from runtime metadata."""
    content = "You are a professional literary translator."
    if metadata:
        content += f"\n\nContext: {metadata}"
    return SystemSection(content=content, metadata=metadata or {})


def build_character(runtime: MergedRuntime) -> CharacterSection:
    """Build Character section from merged runtime character domain."""
    domain = runtime.get_domain("character")
    if domain is None:
        return CharacterSection(content="", metadata={"domain": "character", "entry_count": 0})
    content = _entries_to_content(domain.entries)
    return CharacterSection(
        content=content,
        metadata={"domain": "character", "entry_count": domain.entry_count, "strategy": domain.strategy},
    )


def build_glossary(runtime: MergedRuntime) -> GlossarySection:
    """Build Glossary section from merged runtime glossary domain."""
    domain = runtime.get_domain("glossary")
    if domain is None:
        return GlossarySection(content="", metadata={"domain": "glossary", "entry_count": 0})
    content = _entries_to_content(domain.entries)
    return GlossarySection(
        content=content,
        metadata={"domain": "glossary", "entry_count": domain.entry_count, "strategy": domain.strategy},
    )


def build_scene(runtime: MergedRuntime) -> SceneSection:
    """Build Scene section from merged runtime scene domain."""
    domain = runtime.get_domain("scene")
    if domain is None:
        return SceneSection(content="", metadata={"domain": "scene", "entry_count": 0})
    content = _entries_to_content(domain.entries)
    return SceneSection(
        content=content,
        metadata={"domain": "scene", "entry_count": domain.entry_count, "strategy": domain.strategy},
    )


def build_narrative(runtime: MergedRuntime) -> NarrativeSection:
    """Build Narrative section from merged runtime narrative domain."""
    domain = runtime.get_domain("narrative")
    if domain is None:
        return NarrativeSection(content="", metadata={"domain": "narrative", "entry_count": 0})
    content = _entries_to_content(domain.entries)
    return NarrativeSection(
        content=content,
        metadata={"domain": "narrative", "entry_count": domain.entry_count, "strategy": domain.strategy},
    )


def build_style(runtime: MergedRuntime) -> StyleSection:
    """Build Style section from merged runtime style domain."""
    domain = runtime.get_domain("style")
    if domain is None:
        return StyleSection(content="", metadata={"domain": "style", "entry_count": 0})
    content = _entries_to_content(domain.entries)
    return StyleSection(
        content=content,
        metadata={"domain": "style", "entry_count": domain.entry_count, "strategy": domain.strategy},
    )


def build_chunk(runtime: MergedRuntime, chunk_text: str = "") -> ChunkSection:
    """Build Chunk section with source text to translate."""
    metadata = {"domain": "chunk", "has_text": bool(chunk_text)}
    return ChunkSection(content=chunk_text, metadata=metadata)


SECTION_BUILDERS = {
    "System": build_system,
    "Character": build_character,
    "Glossary": build_glossary,
    "Scene": build_scene,
    "Narrative": build_narrative,
    "Style": build_style,
    "Chunk": build_chunk,
}

__all__ = [
    "build_system",
    "build_character",
    "build_glossary",
    "build_scene",
    "build_narrative",
    "build_style",
    "build_chunk",
    "SECTION_BUILDERS",
]