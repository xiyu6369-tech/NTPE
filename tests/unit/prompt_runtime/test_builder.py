"""Tests for Prompt Runtime builder."""

import pytest

from core.knowledge_runtime.merger import MergedKnowledge, MergedRuntime
from core.prompt_runtime.builder import PromptAssembly, PromptBuilder, build_prompt
from core.prompt_runtime.models import SECTION_ORDER


def make_runtime(domains: dict) -> MergedRuntime:
    """Helper to create MergedRuntime with specified domains."""
    merged_domains = {}
    for name, entries in domains.items():
        merged_domains[name] = MergedKnowledge(
            domain=name,
            entries=entries,
            strategy="key_override",
        )
    return MergedRuntime(domains=merged_domains)


def test_build_prompt_full_assembly():
    """build_prompt assembles all sections in correct order (default: feature OFF)."""
    runtime = make_runtime({
        "character": {"Hero": "knight"},
        "glossary": {"術語": "term"},
        "scene": {"location": "castle"},
        "narrative": {"tone": "dark"},
        "style": {"register": "formal"},
    })
    assembly = build_prompt(runtime, "Source text to translate")

    # Feature OFF: 8 sections (Context not included)
    assert assembly.section_count == 8
    section_names = [s.name for s in assembly.sections]
    # Verify order without Context section
    assert section_names == [
        "System",
        "Character",
        "Entity Mapping",
        "Glossary",
        "Scene",
        "Narrative",
        "Style",
        "Chunk",
    ]


def test_build_prompt_full_assembly_feature_on():
    """build_prompt with enable_cross_chunk_context=True includes Context section (feature ON)."""
    from core.prompt_runtime.builder import PromptBuilder
    from core.context_scene_memory.models import ContextSelectionResult, SelectedContextItem

    runtime = make_runtime({
        "character": {"Hero": "knight"},
        "glossary": {"術語": "term"},
        "scene": {"location": "castle"},
        "narrative": {"tone": "dark"},
        "style": {"register": "formal"},
    })

    # Feature ON: Use PromptBuilder directly with enable_cross_chunk_context=True
    builder = PromptBuilder(
        chunk_text="Source text to translate",
        enable_cross_chunk_context=True,
        context_selection=ContextSelectionResult(
            selected_records=(
                SelectedContextItem(
                    item_id="ctx_1",
                    item_type="scene_summary",
                    value="Previous scene summary",
                    evidence_ids=("ev_1",),
                    estimated_tokens=10,
                    priority=0,
                ),
            ),
            selected_character_memories=(),
            estimated_tokens=10,
            character_estimated_tokens=0,
            budget=512,
            character_budget=256,
            dropped_records=(),
            drop_reasons={},
            deterministic_fingerprint="abc123",
        ),
    )
    assembly = builder.build(runtime)

    # Feature ON: 9 sections (Context included)
    assert assembly.section_count == 9
    section_names = [s.name for s in assembly.sections]
    # Verify full SECTION_ORDER with Context
    assert section_names == list(SECTION_ORDER)

    # Verify Context section content
    context_section = next(s for s in assembly.sections if s.name == "Context")
    assert "Cross-Chunk Context" in context_section.content
    assert "Previous scene summary" in context_section.content


def test_build_prompt_section_order():
    """Sections must be in fixed order: System→Character→Entity Mapping→Glossary→Scene→Narrative→Style→Chunk (feature OFF)."""
    runtime = make_runtime({})
    assembly = build_prompt(runtime, "chunk")
    names = [s.name for s in assembly.sections]
    assert names == [
        "System",
        "Character",
        "Entity Mapping",
        "Glossary",
        "Scene",
        "Narrative",
        "Style",
        "Chunk",
    ]


def test_build_prompt_empty_runtime():
    """build_prompt works with empty runtime (no domains)."""
    runtime = make_runtime({})
    assembly = build_prompt(runtime, "text")
    assert assembly.section_count == 8
    # All domain sections should be empty (skip System, Entity Mapping, Chunk)
    for section in assembly.sections[1:-1]:
        if section.name == "Entity Mapping":
            assert "No entity mappings" in section.content
        else:
            assert section.content == ""
            assert section.metadata["entry_count"] == 0


def test_build_prompt_missing_domains():
    """build_prompt handles missing domains gracefully."""
    runtime = make_runtime({"character": {"Hero": "knight"}})
    assembly = build_prompt(runtime, "text")
    char_section = next(s for s in assembly.sections if s.name == "Character")
    gloss_section = next(s for s in assembly.sections if s.name == "Glossary")
    assert char_section.content == "Hero: knight"
    assert gloss_section.content == ""


def test_build_prompt_chunk_text():
    """Chunk section contains provided source text."""
    runtime = make_runtime({})
    assembly = build_prompt(runtime, "Hello world")
    chunk_section = assembly.sections[-1]
    assert chunk_section.name == "Chunk"
    assert chunk_section.content == "Hello world"
    assert chunk_section.metadata["has_text"] is True


def test_build_prompt_metadata():
    """Assembly metadata includes runtime info."""
    runtime = make_runtime({"character": {"a": "b"}})
    assembly = build_prompt(runtime, "text")
    assert assembly.metadata["runtime_version"] == runtime.version
    assert "character" in assembly.metadata["runtime_domains"]
    assert assembly.metadata["chunk_text_length"] == 4


def test_prompt_builder_class():
    """PromptBuilder class produces same result as build_prompt."""
    runtime = make_runtime({"character": {"Hero": "knight"}})
    builder = PromptBuilder(chunk_text="text")
    assembly1 = builder.build(runtime)
    assembly2 = build_prompt(runtime, "text")
    assert assembly1.section_count == assembly2.section_count
    assert [s.name for s in assembly1.sections] == [s.name for s in assembly2.sections]


def test_prompt_builder_partial():
    """PromptBuilder.build_partial includes only specified sections."""
    runtime = make_runtime({"character": {"Hero": "knight"}, "glossary": {"術語": "term"}})
    builder = PromptBuilder(chunk_text="text")
    assembly = builder.build_partial(runtime, include=["System", "Character", "Chunk"])
    names = [s.name for s in assembly.sections]
    assert names == ["System", "Character", "Chunk"]
    assert assembly.metadata["included_sections"] == ["System", "Character", "Chunk"]


def test_prompt_assembly_serialization_roundtrip():
    """PromptAssembly serializes and deserializes correctly."""
    runtime = make_runtime({"character": {"Hero": "knight"}})
    assembly = build_prompt(runtime, "text")
    data = assembly.to_dict()
    restored = PromptAssembly.from_dict(data)
    assert restored.section_count == assembly.section_count
    assert [s.name for s in restored.sections] == [s.name for s in assembly.sections]
    assert restored.metadata == assembly.metadata


def test_deterministic_output():
    """Same inputs must produce identical assemblies."""
    runtime = make_runtime({"character": {"Hero": "knight"}})
    a1 = build_prompt(runtime, "text")
    a2 = build_prompt(runtime, "text")
    assert a1.to_dict() == a2.to_dict()


def test_system_metadata_propagated():
    """System metadata passed to builder appears in System section."""
    runtime = make_runtime({})
    builder = PromptBuilder(chunk_text="text", system_metadata={"novel": "Test Novel"})
    assembly = builder.build(runtime)
    sys_section = assembly.sections[0]
    assert "Test Novel" in sys_section.content
    assert sys_section.metadata["novel"] == "Test Novel"