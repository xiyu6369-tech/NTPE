"""RM-6.2.0 Prompt Runtime domain models.

Prompt section models for structured prompt assembly.
Immutable, ordered, serializable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True, order=True)
class PromptSection:
    """Base prompt section — immutable, ordered, serializable."""

    name: str
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "rm-6.2.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "content": self.content,
            "metadata": dict(self.metadata),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "PromptSection":
        return cls(
            name=str(payload.get("name", "")),
            content=str(payload.get("content", "")),
            metadata=dict(payload.get("metadata") or {}),
            version=str(payload.get("version", "rm-6.2.0")),
        )

    def __str__(self) -> str:
        return self.content


@dataclass(frozen=True, order=True)
class CharacterSection(PromptSection):
    """Character section for prompt assembly."""

    name: str = "Character"


@dataclass(frozen=True, order=True)
class EntityMappingSection(PromptSection):
    """Entity Mapping section for prompt assembly (RM-7.2)."""

    name: str = "Entity Mapping"


@dataclass(frozen=True, order=True)
class GlossarySection(PromptSection):
    """Glossary section for prompt assembly."""

    name: str = "Glossary"


@dataclass(frozen=True, order=True)
class SceneSection(PromptSection):
    """Scene section for prompt assembly."""

    name: str = "Scene"


@dataclass(frozen=True, order=True)
class NarrativeSection(PromptSection):
    """Narrative section for prompt assembly."""

    name: str = "Narrative"


@dataclass(frozen=True, order=True)
class StyleSection(PromptSection):
    """Style section for prompt assembly."""

    name: str = "Style"


@dataclass(frozen=True, order=True)
class SystemSection(PromptSection):
    """System section for prompt assembly."""

    name: str = "System"


@dataclass(frozen=True, order=True)
class ChunkSection(PromptSection):
    """Chunk section for prompt assembly."""

    name: str = "Chunk"


SECTION_ORDER = (
    "System",
    "Character",
    "Entity Mapping",
    "Glossary",
    "Scene",
    "Narrative",
    "Style",
    "Chunk",
)

SECTION_MAP = {
    "System": SystemSection,
    "Character": CharacterSection,
    "Entity Mapping": EntityMappingSection,
    "Glossary": GlossarySection,
    "Scene": SceneSection,
    "Narrative": NarrativeSection,
    "Style": StyleSection,
    "Chunk": ChunkSection,
}

__all__ = [
    "PromptSection",
    "CharacterSection",
    "EntityMappingSection",
    "GlossarySection",
    "SceneSection",
    "NarrativeSection",
    "StyleSection",
    "SystemSection",
    "ChunkSection",
    "SECTION_ORDER",
    "SECTION_MAP",
]