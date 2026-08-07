"""RM-7.2 Entity Resolver domain models.

Entity resolution models for pre-translation entity mapping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EntityType(Enum):
    """Known entity types for translation."""
    CHARACTER = "CHARACTER"
    PLACE = "PLACE"
    ORGANIZATION = "ORGANIZATION"
    TERMINOLOGY = "TERMINOLOGY"
    UNKNOWN = "UNKNOWN"


class InjectionSource(Enum):
    """Source priority levels for entity resolution (highest to lowest)."""
    USER = "USER"         # User-defined override (highest priority)
    RUNTIME = "RUNTIME"   # Runtime knowledge (merged snapshot)
    LEARNING = "LEARNING" # Learning knowledge (historical patterns)
    AUTO = "AUTO"         # Auto-detected/inferred (lowest priority)


@dataclass(frozen=True)
class ResolvedEntity:
    """A single resolved entity with its standard translation."""

    source: str
    target: str
    entity_type: str = EntityType.UNKNOWN.value
    source_level: str = InjectionSource.AUTO.value
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "rm-7.2.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "entity_type": self.entity_type,
            "source_level": self.source_level,
            "metadata": dict(self.metadata),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ResolvedEntity":
        return cls(
            source=str(payload.get("source", "")),
            target=str(payload.get("target", "")),
            entity_type=str(payload.get("entity_type", EntityType.UNKNOWN.value)),
            source_level=str(payload.get("source_level", InjectionSource.AUTO.value)),
            metadata=dict(payload.get("metadata") or {}),
            version=str(payload.get("version", "rm-7.2.0")),
        )

    @property
    def is_user_override(self) -> bool:
        return self.source_level == InjectionSource.USER.value

    @property
    def is_known(self) -> bool:
        return self.target != "" and self.target != "(No predefined translation)"


@dataclass(frozen=True)
class EntityInjectionSet:
    """Collection of resolved entities for prompt injection."""

    entities: List[ResolvedEntity] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "rm-7.2.0"

    @property
    def count(self) -> int:
        return len(self.entities)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "metadata": dict(self.metadata),
            "version": self.version,
            "count": self.count,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EntityInjectionSet":
        return cls(
            entities=[ResolvedEntity.from_dict(e) for e in payload.get("entities", [])],
            metadata=dict(payload.get("metadata") or {}),
            version=str(payload.get("version", "rm-7.2.0")),
        )

    def get_by_source(self, source: str) -> Optional[ResolvedEntity]:
        for entity in self.entities:
            if entity.source == source:
                return entity
        return None

    def get_known_entities(self) -> List[ResolvedEntity]:
        return [e for e in self.entities if e.is_known]

    def get_unknown_entities(self) -> List[ResolvedEntity]:
        return [e for e in self.entities if not e.is_known]


@dataclass(frozen=True)
class ExtractedEntity:
    """An entity extracted from source text (before resolution)."""

    source: str
    entity_type: str = EntityType.UNKNOWN.value
    context: str = ""
    position: int = -1
    version: str = "rm-7.2.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "entity_type": self.entity_type,
            "context": self.context,
            "position": self.position,
            "version": self.version,
        }


__all__ = [
    "EntityType",
    "InjectionSource",
    "ResolvedEntity",
    "EntityInjectionSet",
    "ExtractedEntity",
    "UNKNOWN_TRANSLATION",
]


# Default unknown translation marker
UNKNOWN_TRANSLATION = "(No predefined translation)"