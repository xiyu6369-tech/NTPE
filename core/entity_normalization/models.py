"""RM-7.3 Entity Normalization — core domain models.

Entity Identity + Surface Form + Context Rule architecture.
Preserves original address levels while ensuring translation consistency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EntityType(Enum):
    """Supported entity types for normalization."""
    CHARACTER = "CHARACTER"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    TERM = "TERM"


class NameFormType(Enum):
    """Types of name surface forms for characters."""
    FULL_NAME = "FULL_NAME"
    GIVEN_NAME = "GIVEN_NAME"
    FAMILY_NAME = "FAMILY_NAME"
    NICKNAME = "NICKNAME"
    TITLE = "TITLE"
    FORMAL = "FORMAL"
    INTIMATE = "INTIMATE"
    RELATIONSHIP = "RELATIONSHIP"


class ConflictSeverity(Enum):
    """Severity levels for normalization conflicts."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ResolutionSource(Enum):
    """Source priority for conflict resolution (highest to lowest)."""
    USER = "USER"
    RUNTIME = "RUNTIME"
    LEARNING = "LEARNING"
    AUTO = "AUTO"


@dataclass(frozen=True)
class NameFormTranslation:
    """A single surface form with its translation."""
    source: str
    translation: str
    form_type: NameFormType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "translation": self.translation,
            "form_type": self.form_type.value,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NameFormTranslation":
        return cls(
            source=str(data["source"]),
            translation=str(data["translation"]),
            form_type=NameFormType(str(data["form_type"])),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class EntityNameForms:
    """All known surface forms for a single entity."""
    full_name: Optional[NameFormTranslation] = None
    given_name: Optional[NameFormTranslation] = None
    family_name: Optional[NameFormTranslation] = None
    nicknames: List[NameFormTranslation] = field(default_factory=list)
    titles: List[NameFormTranslation] = field(default_factory=list)
    formal: Optional[NameFormTranslation] = None
    intimate: Optional[NameFormTranslation] = None
    relationship: List[NameFormTranslation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_form(self, form_type: NameFormType) -> Optional[NameFormTranslation]:
        """Get a specific form by type."""
        if form_type == NameFormType.FULL_NAME:
            return self.full_name
        elif form_type == NameFormType.GIVEN_NAME:
            return self.given_name
        elif form_type == NameFormType.FAMILY_NAME:
            return self.family_name
        elif form_type == NameFormType.FORMAL:
            return self.formal
        elif form_type == NameFormType.INTIMATE:
            return self.intimate
        return None

    def get_all_forms(self) -> List[NameFormTranslation]:
        """Get all forms as a flat list."""
        forms = []
        for attr in ["full_name", "given_name", "family_name", "formal", "intimate"]:
            val = getattr(self, attr)
            if val:
                forms.append(val)
        forms.extend(self.nicknames)
        forms.extend(self.titles)
        forms.extend(self.relationship)
        return forms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "full_name": self.full_name.to_dict() if self.full_name else None,
            "given_name": self.given_name.to_dict() if self.given_name else None,
            "family_name": self.family_name.to_dict() if self.family_name else None,
            "nicknames": [n.to_dict() for n in self.nicknames],
            "titles": [t.to_dict() for t in self.titles],
            "formal": self.formal.to_dict() if self.formal else None,
            "intimate": self.intimate.to_dict() if self.intimate else None,
            "relationship": [r.to_dict() for r in self.relationship],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityNameForms":
        return cls(
            full_name=NameFormTranslation.from_dict(data["full_name"]) if data.get("full_name") else None,
            given_name=NameFormTranslation.from_dict(data["given_name"]) if data.get("given_name") else None,
            family_name=NameFormTranslation.from_dict(data["family_name"]) if data.get("family_name") else None,
            nicknames=[NameFormTranslation.from_dict(n) for n in data.get("nicknames", [])],
            titles=[NameFormTranslation.from_dict(t) for t in data.get("titles", [])],
            formal=NameFormTranslation.from_dict(data["formal"]) if data.get("formal") else None,
            intimate=NameFormTranslation.from_dict(data["intimate"]) if data.get("intimate") else None,
            relationship=[NameFormTranslation.from_dict(r) for r in data.get("relationship", [])],
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class CanonicalEntity:
    """Unique entity identity with canonical translation."""
    entity_id: str
    entity_type: EntityType
    source_name: str
    canonical_translation: str
    name_forms: EntityNameForms
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    version: str = "rm-7.3.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "source_name": self.source_name,
            "canonical_translation": self.canonical_translation,
            "name_forms": self.name_forms.to_dict(),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanonicalEntity":
        return cls(
            entity_id=str(data["entity_id"]),
            entity_type=EntityType(str(data["entity_type"])),
            source_name=str(data["source_name"]),
            canonical_translation=str(data["canonical_translation"]),
            name_forms=EntityNameForms.from_dict(data["name_forms"]),
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", utc_now_iso())),
            updated_at=str(data.get("updated_at", utc_now_iso())),
            version=str(data.get("version", "rm-7.3.0")),
        )


@dataclass(frozen=True)
class ConflictRecord:
    """A conflict between candidate translations for the same source."""
    source: str
    entity_type: EntityType
    candidates: List[str]
    severity: ConflictSeverity = ConflictSeverity.HIGH
    resolution: Optional[str] = None
    resolution_source: Optional[ResolutionSource] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    @property
    def is_resolved(self) -> bool:
        return self.resolution is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "entity_type": self.entity_type.value,
            "candidates": list(self.candidates),
            "severity": self.severity.value,
            "resolution": self.resolution,
            "resolution_source": self.resolution_source.value if self.resolution_source else None,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConflictRecord":
        return cls(
            source=str(data["source"]),
            entity_type=EntityType(str(data["entity_type"])),
            candidates=list(data.get("candidates", [])),
            severity=ConflictSeverity(str(data.get("severity", "HIGH"))),
            resolution=data.get("resolution"),
            resolution_source=ResolutionSource(str(data["resolution_source"])) if data.get("resolution_source") else None,
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", utc_now_iso())),
        )


@dataclass(frozen=True)
class NormalizationContext:
    """Context for name form resolution."""
    source_text: str
    position: int
    surrounding_text: str = ""
    speaker: Optional[str] = None
    listener: Optional[str] = None
    relationship_hint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_text": self.source_text,
            "position": self.position,
            "surrounding_text": self.surrounding_text,
            "speaker": self.speaker,
            "listener": self.listener,
            "relationship_hint": self.relationship_hint,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class NormalizedEntity:
    """Result of entity normalization for a specific occurrence."""
    source_text: str
    entity_id: str
    entity_type: EntityType
    matched_form: NameFormTranslation
    translation: str
    confidence: float = 1.0
    context: Optional[NormalizationContext] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_text": self.source_text,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "matched_form": self.matched_form.to_dict(),
            "translation": self.translation,
            "confidence": self.confidence,
            "context": self.context.to_dict() if self.context else None,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class NormalizationResult:
    """Collection of normalized entities from a text chunk."""
    entities: List[NormalizedEntity] = field(default_factory=list)
    conflicts: List[ConflictRecord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_entity(self, entity: NormalizedEntity) -> "NormalizationResult":
        return NormalizationResult(
            entities=self.entities + [entity],
            conflicts=list(self.conflicts),
            metadata=dict(self.metadata),
        )

    def add_conflict(self, conflict: ConflictRecord) -> "NormalizationResult":
        return NormalizationResult(
            entities=list(self.entities),
            conflicts=self.conflicts + [conflict],
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "metadata": dict(self.metadata),
        }


__all__ = [
    "EntityType",
    "NameFormType",
    "ConflictSeverity",
    "ResolutionSource",
    "NameFormTranslation",
    "EntityNameForms",
    "CanonicalEntity",
    "ConflictRecord",
    "NormalizationContext",
    "NormalizedEntity",
    "NormalizationResult",
]