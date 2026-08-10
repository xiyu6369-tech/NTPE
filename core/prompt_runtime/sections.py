"""RM-6.2.0 Prompt Runtime section builders.

Each domain has an independent builder function that transforms
MergedRuntime domain data into structured PromptSection objects.

RM-8.2 Extensions (feature-gated):
- build_context_selection: New Context section for cross-chunk context
- build_character, build_scene, build_narrative: Parameterized for RM-8.2
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.context_scene_memory.models import (
    ContextSelectionResult, CharacterContextItem, SceneMemoryRecord,
    ParticipantStatus, ResolutionStatus, UnresolvedReference, SceneParticipant,
)
from core.knowledge_runtime.merger import MergedRuntime
from core.prompt_runtime.models import (
    CharacterSection,
    ChunkSection,
    ContextSection,
    EntityMappingSection,
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


def build_context_selection(selection: Optional[ContextSelectionResult]) -> ContextSection:
    """Build Context section from token-budgeted selection. NEW SECTION for RM-8.2."""
    if not selection or not selection.selected_records:
        return ContextSection(
            content="No relevant context from prior chunks.",
            metadata={"source": "context_selection", "record_count": 0}
        )

    lines = ["【Cross-Chunk Context】"]
    for item in selection.selected_records:
        # item: SelectedContextItem { item_id, item_type, value, evidence_ids, estimated_tokens, priority }
        lines.append(f"- {item.value}")

    content = "\n".join(lines)
    return ContextSection(
        content=content,
        metadata={
            "source": "context_selection",
            "record_count": len(selection.selected_records),
            "estimated_tokens": selection.estimated_tokens,
            "fingerprint": selection.deterministic_fingerprint,
        }
    )


def build_character(
    runtime: MergedRuntime,
    character_memories: Optional[Tuple[CharacterContextItem, ...]] = None
) -> CharacterSection:
    """Build Character section from merged runtime character domain, optionally extended with selected character memories."""
    domain = runtime.get_domain("character")
    if domain is None:
        base_content = ""
    else:
        base_content = _entries_to_content(domain.entries)

    if not character_memories:
        return CharacterSection(
            content=base_content,
            metadata={"domain": "character", "entry_count": domain.entry_count if domain else 0, "strategy": domain.strategy if domain else ""},
        )

    char_lines = [base_content] if base_content else []
    char_lines.append("\n【Active Character Memories】")
    for item in character_memories:
        # item: CharacterContextItem { memory_id, character_id, fact_type, value, evidence_ids, estimated_tokens }
        char_lines.append(f"- {item.character_id} ({item.fact_type}): {item.value}")

    return CharacterSection(
        content="\n".join(char_lines),
        metadata={
            "domain": "character",
            "entry_count": domain.entry_count if domain else 0,
            "strategy": domain.strategy if domain else "",
            "selected_memory_count": len(character_memories),
            "character_tokens": sum(item.estimated_tokens for item in character_memories),
        }
    )


def build_entity_mapping(
    runtime: MergedRuntime,
    injection_set: Optional[Any] = None,
) -> EntityMappingSection:
    """Build Entity Mapping section from entity injection set (RM-7.2).

    Args:
        runtime: MergedRuntime (for metadata)
        injection_set: EntityInjectionSet from entity_resolver (optional)

    Returns:
        EntityMappingSection with resolved entity mappings
    """
    if injection_set is None:
        return EntityMappingSection(
            content="No entity mappings available for this chunk.",
            metadata={"entity_count": 0, "source": "none"},
        )

    # Handle both EntityInjectionSet and PromptSection (already formatted)
    if hasattr(injection_set, "entities"):
        # It's an EntityInjectionSet
        known_entities = [e for e in injection_set.entities if e.is_known]
        unknown_entities = [e for e in injection_set.entities if not e.is_known]

        if not known_entities and not unknown_entities:
            content = "No entities found in current chunk."
        else:
            lines = []
            if known_entities:
                lines.append("Known Entities:")
                for entity in known_entities:
                    marker = " [USER OVERRIDE]" if entity.is_user_override else ""
                    lines.append(f"  {entity.source} → {entity.target}{marker}")
            if unknown_entities:
                lines.append("\nUnknown Entities (no predefined translation):")
                for entity in unknown_entities:
                    lines.append(f"  {entity.source} → (No predefined translation)")
            content = "\n".join(lines)

        metadata = {
            "entity_count": injection_set.count,
            "known_count": len(known_entities),
            "unknown_count": len(unknown_entities),
            "source_breakdown": injection_set.metadata,
        }
    elif hasattr(injection_set, "content"):
        # It's already a PromptSection
        content = injection_set.content
        metadata = dict(injection_set.metadata)
    else:
        content = str(injection_set)
        metadata = {"entity_count": 0, "source": "unknown"}

    return EntityMappingSection(content=content, metadata=metadata)


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


def build_scene(
    runtime: MergedRuntime,
    scene_state: Optional[SceneMemoryRecord] = None
) -> SceneSection:
    """Build Scene section from merged runtime scene domain, optionally extended with live SceneMemoryRecord."""
    if not scene_state:
        domain = runtime.get_domain("scene")
        if domain is None:
            return SceneSection(content="", metadata={"domain": "scene", "entry_count": 0})
        content = _entries_to_content(domain.entries)
        return SceneSection(
            content=content,
            metadata={"domain": "scene", "entry_count": domain.entry_count, "strategy": domain.strategy},
        )

    parts = []
    if scene_state.location:
        parts.append(f"場景={scene_state.location}")
    if scene_state.time_state:
        parts.append(f"時間={scene_state.time_state}")
    if scene_state.active_speaker:
        parts.append(f"發言者={scene_state.active_speaker}")
    if scene_state.point_of_view:
        parts.append(f"視點={scene_state.point_of_view}")
    if scene_state.event_state:
        parts.append(f"事件={'、'.join(scene_state.event_state[-5:])}")

    content = "；".join(parts) if parts else ""

    # Add participants
    if scene_state.participants:
        present = [p.character_id for p in scene_state.participants
                   if p.participant_status == ParticipantStatus.PRESENT]
        if present:
            content += f"\n在場人物：{'、'.join(present)}"

    # Add unresolved references
    unresolved = [r for r in scene_state.unresolved_references
                  if r.resolution_status in {ResolutionStatus.UNRESOLVED, ResolutionStatus.CANDIDATE}]
    if unresolved:
        ref_lines = ["未解析指代："]
        for r in unresolved[:5]:
            ref_lines.append(f"  {r.surface_form}" + (f"→{r.resolved_target}" if r.resolved_target else ""))
        content += "\n" + "\n".join(ref_lines)

    return SceneSection(
        content=content,
        metadata={
            "domain": "scene",
            "scene_id": scene_state.scene_id,
            "scene_version": scene_state.scene_version,
            "chapter_id": scene_state.chapter_id,
            "participant_count": len(scene_state.participants),
            "unresolved_count": len(unresolved),
        }
    )


def build_narrative(
    runtime: MergedRuntime,
    narrative_state: Optional[dict] = None
) -> NarrativeSection:
    """Build Narrative section from merged runtime narrative domain, optionally extended with NarrativeIntelligenceEngine context."""
    if not narrative_state:
        domain = runtime.get_domain("narrative")
        if domain is None:
            return NarrativeSection(content="", metadata={"domain": "narrative", "entry_count": 0})
        content = _entries_to_content(domain.entries)
        return NarrativeSection(
            content=content,
            metadata={"domain": "narrative", "entry_count": domain.entry_count, "strategy": domain.strategy},
        )

    lines = []
    if narrative_state.get("perspective"):
        lines.append(f"視點：{narrative_state['perspective']}")
    if narrative_state.get("voice"):
        lines.append(f"語氣：{narrative_state['voice']}")
    if narrative_state.get("tense"):
        lines.append(f"時制：{narrative_state['tense']}")
    if narrative_state.get("emotional_tone"):
        lines.append(f"情感基調：{narrative_state['emotional_tone']}")
    if narrative_state.get("focus"):
        lines.append(f"敘事焦點：{narrative_state['focus']}")
    if narrative_state.get("transitions"):
        lines.append(f"場景轉換：{' → '.join(narrative_state['transitions'][-3:])}")

    content = "\n".join(lines)
    return NarrativeSection(
        content=content,
        metadata={
            "domain": "narrative",
            "source": "narrative_intelligence",
            **narrative_state.get("metadata", {})
        }
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
    "Context": build_context_selection,
    "Chunk": build_chunk,
}

__all__ = [
    "build_system",
    "build_character",
    "build_entity_mapping",
    "build_glossary",
    "build_scene",
    "build_narrative",
    "build_style",
    "build_chunk",
    "build_context_selection",
    "SECTION_BUILDERS",
]