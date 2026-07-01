"""Foundation-08.0 Knowledge Layer contracts.

This module defines runtime-safe, storage-agnostic contracts for the NTPE
Knowledge Layer. The contract intentionally uses plain dictionaries so it can
be adopted incrementally without breaking Foundation-07 intelligence modules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


def utc_now_iso() -> str:
    """Return a stable UTC timestamp for contract metadata."""

    return datetime.now(timezone.utc).isoformat()


@dataclass
class KnowledgeItem:
    """Single normalized knowledge entry."""

    key: str
    value: Any
    domain: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "domain": self.domain,
            "metadata": dict(self.metadata),
            "source": self.source,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "KnowledgeItem":
        return cls(
            key=str(payload.get("key", "")),
            value=payload.get("value"),
            domain=str(payload.get("domain", "general")),
            metadata=dict(payload.get("metadata") or {}),
            source=payload.get("source"),
            updated_at=str(payload.get("updated_at") or utc_now_iso()),
        )


class KnowledgeRepository(ABC):
    """Storage-agnostic repository contract for Knowledge Layer implementations."""

    @abstractmethod
    def put(self, item: KnowledgeItem) -> KnowledgeItem:
        """Insert or update a knowledge item."""

    @abstractmethod
    def get(self, key: str, domain: str = "general") -> Optional[KnowledgeItem]:
        """Return a knowledge item by domain and key."""

    @abstractmethod
    def query(self, query: "KnowledgeQuery") -> List[KnowledgeItem]:
        """Return all items matching the supplied query object."""

    @abstractmethod
    def delete(self, key: str, domain: str = "general") -> bool:
        """Delete an item and return whether something was removed."""

    @abstractmethod
    def snapshot(self, name: str = "default") -> "KnowledgeSnapshot":
        """Create a portable snapshot of the repository state."""

    @abstractmethod
    def manifest(self) -> "KnowledgeManifest":
        """Return repository capabilities and version metadata."""


class KnowledgeProvider(ABC):
    """Read-only provider contract for Runtime, Prompt Pipeline, and Plugins."""

    @abstractmethod
    def provide(self, query: "KnowledgeQuery") -> List[KnowledgeItem]:
        """Provide knowledge without exposing repository internals."""

    @abstractmethod
    def build_context(self, query: Optional["KnowledgeQuery"] = None) -> Dict[str, Any]:
        """Build a prompt/runtime-safe context dictionary."""


@dataclass
class KnowledgeQuery:
    """Normalized query contract for the Knowledge Layer."""

    text: str = ""
    domain: Optional[str] = None
    keys: List[str] = field(default_factory=list)
    limit: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches(self, item: KnowledgeItem) -> bool:
        if self.domain and item.domain != self.domain:
            return False
        if self.keys and item.key not in self.keys:
            return False
        if self.text:
            haystack = f"{item.key} {item.value} {item.domain}".lower()
            if self.text.lower() not in haystack:
                return False
        for key, value in self.metadata.items():
            if item.metadata.get(key) != value:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "domain": self.domain,
            "keys": list(self.keys),
            "limit": self.limit,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "KnowledgeQuery":
        payload = payload or {}
        return cls(
            text=str(payload.get("text", "")),
            domain=payload.get("domain"),
            keys=list(payload.get("keys") or []),
            limit=payload.get("limit"),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass
class KnowledgeSnapshot:
    """Portable, versioned Knowledge Layer snapshot."""

    name: str = "default"
    version: str = "foundation-08.0"
    items: List[KnowledgeItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "items": [item.to_dict() for item in self.items],
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "KnowledgeSnapshot":
        return cls(
            name=str(payload.get("name", "default")),
            version=str(payload.get("version", "foundation-08.0")),
            items=[KnowledgeItem.from_dict(item) for item in payload.get("items", [])],
            metadata=dict(payload.get("metadata") or {}),
            created_at=str(payload.get("created_at") or utc_now_iso()),
        )


@dataclass
class KnowledgeManifest:
    """Repository/provider capability manifest."""

    name: str = "knowledge_contract"
    version: str = "foundation-08.0"
    enabled: bool = True
    capabilities: List[str] = field(default_factory=lambda: [
        "put",
        "get",
        "query",
        "delete",
        "snapshot",
        "manifest",
        "runtime_context",
    ])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }


class KnowledgeRegistryContract(ABC):
    """Registry contract for swapping repository implementations safely."""

    @abstractmethod
    def register(self, name: str, repository: KnowledgeRepository, default: bool = False) -> None:
        """Register a repository implementation."""

    @abstractmethod
    def get(self, name: Optional[str] = None) -> KnowledgeRepository:
        """Return a named or default repository."""

    @abstractmethod
    def list(self) -> List[str]:
        """List repository names."""
