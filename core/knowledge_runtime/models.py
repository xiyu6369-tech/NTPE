"""RM-6.1.0 Knowledge Runtime domain models.

Architecture-only datamodels. No provider imports.
No feedback integration. No benchmark modifications.
Completely offline runtime by design.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeDomain(Enum):
    CHARACTER = auto()
    GLOSSARY = auto()
    NARRATIVE = auto()
    SCENE = auto()
    STYLE = auto()
    GENERAL = auto()


@dataclass(frozen=True)
class KnowledgePrototype:
    """Immutable prototype used during load/resolve handoffs.

    This is deliberately NOT a provider contract — providers are
    excluded from RM-6.1 per the offline-only constraint.
    """

    key: str
    domain: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "rm-6.1.0"


@dataclass(frozen=True)
class KnowledgeEntry:
    """Resolved knowledge entry ready for runtime consumption."""

    key: str
    value: Any
    domain: str = "general"
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved_at: str = field(default_factory=utc_now_iso)
    version: str = "rm-6.1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "domain": self.domain,
            "source": self.source,
            "metadata": dict(self.metadata),
            "resolved_at": self.resolved_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "KnowledgeEntry":
        return cls(
            key=str(payload.get("key", "")),
            value=payload.get("value"),
            domain=str(payload.get("domain", "general")),
            source=str(payload.get("source", "")),
            metadata=dict(payload.get("metadata") or {}),
            resolved_at=str(payload.get("resolved_at") or utc_now_iso()),
            version=str(payload.get("version", "rm-6.1.0")),
        )


@dataclass(frozen=True)
class KnowledgeBundle:
    """Collection of entries grouped by domain for a translation segment."""

    id: str = ""
    entries: List[KnowledgeEntry] = field(default_factory=list)
    domain: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    version: str = "rm-6.1.0"

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entries": [entry.to_dict() for entry in self.entries],
            "domain": self.domain,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "version": self.version,
            "entry_count": self.entry_count,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "KnowledgeBundle":
        return cls(
            id=str(payload.get("id", "")),
            entries=[KnowledgeEntry.from_dict(e) for e in payload.get("entries", [])],
            domain=str(payload.get("domain", "general")),
            metadata=dict(payload.get("metadata") or {}),
            created_at=str(payload.get("created_at") or utc_now_iso()),
            version=str(payload.get("version", "rm-6.1.0")),
        )


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """Full-point-in-time snapshot of the knowledge runtime state."""

    id: str = ""
    bundles: List[KnowledgeBundle] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    version: str = "rm-6.1.0"

    @property
    def bundle_count(self) -> int:
        return len(self.bundles)

    @property
    def entry_count(self) -> int:
        return sum(bundle.entry_count for bundle in self.bundles)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "bundles": [b.to_dict() for b in self.bundles],
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "version": self.version,
            "bundle_count": self.bundle_count,
            "entry_count": self.entry_count,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "KnowledgeSnapshot":
        return cls(
            id=str(payload.get("id", "")),
            bundles=[KnowledgeBundle.from_dict(b) for b in payload.get("bundles", [])],
            metadata=dict(payload.get("metadata") or {}),
            created_at=str(payload.get("created_at") or utc_now_iso()),
            version=str(payload.get("version", "rm-6.1.0")),
        )