"""Tests for Prompt Runtime models."""

from dataclasses import FrozenInstanceError

import pytest

from core.prompt_runtime.models import (
    CharacterSection,
    ChunkSection,
    GlossarySection,
    NarrativeSection,
    PromptSection,
    SceneSection,
    SECTION_MAP,
    SECTION_ORDER,
    StyleSection,
    SystemSection,
)


def test_section_order_constant():
    """SECTION_ORDER must match required sequence."""
    assert SECTION_ORDER == (
        "System",
        "Character",
        "Glossary",
        "Scene",
        "Narrative",
        "Style",
        "Chunk",
    )


def test_section_map_complete():
    """SECTION_MAP must contain all required sections."""
    expected = {"System", "Character", "Glossary", "Scene", "Narrative", "Style", "Chunk"}
    assert set(SECTION_MAP.keys()) == expected


def test_all_sections_are_frozen():
    """All section types must be immutable (frozen dataclass)."""
    sections = [
        SystemSection(content="sys"),
        CharacterSection(content="char"),
        GlossarySection(content="gloss"),
        SceneSection(content="scene"),
        NarrativeSection(content="narr"),
        StyleSection(content="style"),
        ChunkSection(content="chunk"),
    ]
    for section in sections:
        with pytest.raises(FrozenInstanceError):
            section.content = "modified"


def test_all_sections_ordered():
    """All sections must support ordering (order=True)."""
    a = SystemSection(content="a")
    b = SystemSection(content="b")
    assert a < b  # frozen + order=True enables comparison


def test_section_serialization_roundtrip():
    """All sections must serialize and deserialize correctly."""
    original = CharacterSection(
        content="Hero: brave knight\nVillain: dark wizard",
        metadata={"domain": "character", "entry_count": 2},
    )
    data = original.to_dict()
    restored = CharacterSection.from_dict(data)
    assert restored == original
    assert restored.name == "Character"
    assert restored.content == original.content
    assert restored.metadata == original.metadata


def test_section_default_name_assignment():
    """Each section type must have correct default name."""
    assert SystemSection().name == "System"
    assert CharacterSection().name == "Character"
    assert GlossarySection().name == "Glossary"
    assert SceneSection().name == "Scene"
    assert NarrativeSection().name == "Narrative"
    assert StyleSection().name == "Style"
    assert ChunkSection().name == "Chunk"


def test_base_prompt_section_serialization():
    """Base PromptSection must serialize correctly."""
    section = PromptSection(name="Custom", content="test", metadata={"key": "value"})
    data = section.to_dict()
    assert data["name"] == "Custom"
    assert data["content"] == "test"
    assert data["metadata"] == {"key": "value"}
    restored = PromptSection.from_dict(data)
    assert restored == section


def test_empty_section_serialization():
    """Empty sections must serialize correctly."""
    section = GlossarySection(content="", metadata={"domain": "glossary", "entry_count": 0})
    data = section.to_dict()
    assert data["content"] == ""
    assert data["metadata"]["entry_count"] == 0