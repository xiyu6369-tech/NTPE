"""Tests for Prompt Runtime section builders."""

import pytest

from core.knowledge_runtime.merger import MergedKnowledge, MergedRuntime
from core.prompt_runtime.sections import (
    build_chunk,
    build_character,
    build_glossary,
    build_narrative,
    build_scene,
    build_style,
    build_system,
    SECTION_BUILDERS,
)


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


def test_build_system_with_metadata():
    """System section includes metadata in content."""
    runtime = make_runtime({})
    section = build_system(runtime, {"project": "test-novel"})
    assert section.name == "System"
    assert "professional literary translator" in section.content
    assert "test-novel" in section.content
    assert section.metadata["project"] == "test-novel"


def test_build_system_without_metadata():
    """System section works without metadata."""
    runtime = make_runtime({})
    section = build_system(runtime)
    assert section.name == "System"
    assert "professional literary translator" in section.content


def test_build_character_with_entries():
    """Character section formats entries correctly."""
    runtime = make_runtime({
        "character": {"Hero": "A brave knight", "Villain": "Dark wizard"}
    })
    section = build_character(runtime)
    assert section.name == "Character"
    assert "Hero: A brave knight" in section.content
    assert "Villain: Dark wizard" in section.content
    assert section.metadata["entry_count"] == 2


def test_build_character_missing_domain():
    """Character section handles missing domain gracefully."""
    runtime = make_runtime({})
    section = build_character(runtime)
    assert section.name == "Character"
    assert section.content == ""
    assert section.metadata["entry_count"] == 0


def test_build_glossary_with_entries():
    """Glossary section formats entries correctly."""
    runtime = make_runtime({
        "glossary": {"術語": "term", "專有名詞": "proper noun"}
    })
    section = build_glossary(runtime)
    assert section.name == "Glossary"
    assert "術語: term" in section.content
    assert section.metadata["entry_count"] == 2


def test_build_glossary_missing_domain():
    """Glossary section handles missing domain."""
    runtime = make_runtime({})
    section = build_glossary(runtime)
    assert section.content == ""
    assert section.metadata["entry_count"] == 0


def test_build_scene_with_entries():
    """Scene section formats entries correctly."""
    runtime = make_runtime({
        "scene": {"location": "ancient castle", "time": "midnight"}
    })
    section = build_scene(runtime)
    assert section.name == "Scene"
    assert "location: ancient castle" in section.content
    assert section.metadata["entry_count"] == 2


def test_build_narrative_with_entries():
    """Narrative section formats entries correctly."""
    runtime = make_runtime({
        "narrative": {"tone": "melancholic", "perspective": "third person"}
    })
    section = build_narrative(runtime)
    assert section.name == "Narrative"
    assert "tone: melancholic" in section.content
    assert section.metadata["entry_count"] == 2


def test_build_style_with_entries():
    """Style section formats entries correctly."""
    runtime = make_runtime({
        "style": {"register": "formal", "length": "detailed"}
    })
    section = build_style(runtime)
    assert section.name == "Style"
    assert "register: formal" in section.content
    assert section.metadata["entry_count"] == 2


def test_build_chunk_with_text():
    """Chunk section includes source text."""
    runtime = make_runtime({})
    section = build_chunk(runtime, "Once upon a time...")
    assert section.name == "Chunk"
    assert section.content == "Once upon a time..."
    assert section.metadata["has_text"] is True


def test_build_chunk_empty_text():
    """Chunk section handles empty text."""
    runtime = make_runtime({})
    section = build_chunk(runtime, "")
    assert section.content == ""
    assert section.metadata["has_text"] is False


def test_all_builders_in_map():
    """SECTION_BUILDERS must contain all required builders."""
    required = {"System", "Character", "Glossary", "Scene", "Narrative", "Style", "Chunk"}
    assert set(SECTION_BUILDERS.keys()) == required


def test_builders_return_correct_types():
    """Each builder returns its corresponding section type."""
    runtime = make_runtime({})
    assert build_system(runtime).__class__.__name__ == "SystemSection"
    assert build_character(runtime).__class__.__name__ == "CharacterSection"
    assert build_glossary(runtime).__class__.__name__ == "GlossarySection"
    assert build_scene(runtime).__class__.__name__ == "SceneSection"
    assert build_narrative(runtime).__class__.__name__ == "NarrativeSection"
    assert build_style(runtime).__class__.__name__ == "StyleSection"
    assert build_chunk(runtime).__class__.__name__ == "ChunkSection"