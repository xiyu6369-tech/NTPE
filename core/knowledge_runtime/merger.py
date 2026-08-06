"""RM-6.1.2 Knowledge Merge Engine — unified runtime view.

No provider imports. Pure offline merge of layered snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .errors import KnowledgeManagerError
from .models import KnowledgeBundle, KnowledgeEntry, KnowledgeSnapshot
from .snapshot import SnapshotHierarchy


class MergeStrategy:
    """Enumeration of merge strategies per domain."""

    KEY_OVERRIDE = "key_override"
    REPLACE = "replace"


# Domain -> Strategy mapping
DOMAIN_STRATEGIES: Dict[str, str] = {
    "character": MergeStrategy.KEY_OVERRIDE,
    "glossary": MergeStrategy.KEY_OVERRIDE,
    "scene": MergeStrategy.REPLACE,
    "narrative": MergeStrategy.REPLACE,
    "style": MergeStrategy.REPLACE,
}


@dataclass(frozen=True)
class MergedKnowledge:
    """Merged knowledge view for a single domain."""

    domain: str
    entries: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    strategy: str = MergeStrategy.KEY_OVERRIDE
    version: str = "rm-6.1.2"

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "entries": dict(self.entries),
            "metadata": dict(self.metadata),
            "strategy": self.strategy,
            "version": self.version,
            "entry_count": self.entry_count,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "MergedKnowledge":
        return cls(
            domain=str(payload.get("domain", "general")),
            entries=dict(payload.get("entries", {})),
            metadata=dict(payload.get("metadata", {})),
            strategy=str(payload.get("strategy", MergeStrategy.KEY_OVERRIDE)),
            version=str(payload.get("version", "rm-6.1.2")),
        )


@dataclass(frozen=True)
class MergedRuntime:
    """Complete merged runtime view across all domains."""

    domains: Dict[str, MergedKnowledge] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "rm-6.1.2"

    @property
    def domain_count(self) -> int:
        return len(self.domains)

    @property
    def total_entries(self) -> int:
        return sum(dk.entry_count for dk in self.domains.values())

    def get_domain(self, domain: str) -> Optional[MergedKnowledge]:
        return self.domains.get(domain)

    def resolve(self, key: str, domain: str = "general") -> Any:
        """Resolve a key from the merged runtime."""
        merged_domain = self.domains.get(domain)
        if merged_domain is None:
            return None
        return merged_domain.entries.get(key)

    def resolve_all(self, domain: str) -> Dict[str, Any]:
        """Resolve all keys for a domain from the merged runtime."""
        merged_domain = self.domains.get(domain)
        if merged_domain is None:
            return {}
        return dict(merged_domain.entries)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domains": {k: v.to_dict() for k, v in self.domains.items()},
            "metadata": dict(self.metadata),
            "version": self.version,
            "domain_count": self.domain_count,
            "total_entries": self.total_entries,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "MergedRuntime":
        domains = {
            k: MergedKnowledge.from_dict(v)
            for k, v in payload.get("domains", {}).items()
        }
        return cls(
            domains=domains,
            metadata=dict(payload.get("metadata", {})),
            version=str(payload.get("version", "rm-6.1.2")),
        )


class KnowledgeMerger:
    """Merge layered snapshots into a unified runtime view.

    The merger accepts snapshots organized by hierarchy level
    (Novel → Volume → Chapter → Chunk) and produces a single
    MergedRuntime that Resolvers query exclusively.
    """

    version = "rm-6.1.2"

    def __init__(self):
        self._hierarchy = SnapshotHierarchy()
        self._merged: Optional[MergedRuntime] = None

    def set_novel(self, domain: str, entries: Dict[str, Any]) -> "KnowledgeMerger":
        """Set Novel-level entries for a domain."""
        self._hierarchy.set_novel(domain, entries)
        return self

    def set_volume(self, domain: str, entries: Dict[str, Any]) -> "KnowledgeMerger":
        """Set Volume-level entries for a domain."""
        self._hierarchy.set_volume(domain, entries)
        return self

    def set_chapter(self, domain: str, entries: Dict[str, Any]) -> "KnowledgeMerger":
        """Set Chapter-level entries for a domain."""
        self._hierarchy.set_chapter(domain, entries)
        return self

    def set_chunk(self, domain: str, entries: Dict[str, Any]) -> "KnowledgeMerger":
        """Set Chunk-level entries for a domain."""
        self._hierarchy.set_chunk(domain, entries)
        return self

    def merge_domain(
        self,
        domain: str,
        strategy: Optional[str] = None,
    ) -> MergedKnowledge:
        """Merge a single domain through the hierarchy.

        Args:
            domain: Domain name (character, glossary, scene, narrative, style)
            strategy: Optional override strategy. Defaults to DOMAIN_STRATEGIES.

        Returns:
            MergedKnowledge for the domain.
        """
        strategy = strategy or DOMAIN_STRATEGIES.get(domain, MergeStrategy.KEY_OVERRIDE)
        merged_entries = self._hierarchy.resolve_all(domain)

        if strategy == MergeStrategy.REPLACE:
            # For REPLACE strategy, only the lowest non-empty level wins
            merged_entries = self._apply_replace_strategy(domain)

        return MergedKnowledge(
            domain=domain,
            entries=merged_entries,
            strategy=strategy,
            version=self.version,
        )

    def _apply_replace_strategy(self, domain: str) -> Dict[str, Any]:
        """Apply REPLACE strategy: lowest non-empty level completely replaces higher levels."""
        for level in reversed(SnapshotHierarchy.ORDER):
            layer = self._hierarchy._layers[level]
            domain_entries = layer.get(domain, {})
            if domain_entries:
                return dict(domain_entries)
        return {}

    def merge_bundle(self, bundle: KnowledgeBundle) -> MergedKnowledge:
        """Merge a KnowledgeBundle into the hierarchy and return merged domain."""
        domain = bundle.domain
        entries = {entry.key: entry.value for entry in bundle.entries}
        self._hierarchy.set_chunk(domain, entries)
        return self.merge_domain(domain)

    def merge_snapshot(self, snapshot: KnowledgeSnapshot) -> MergedRuntime:
        """Merge all bundles from a snapshot into the hierarchy."""
        for bundle in snapshot.bundles:
            entries = {entry.key: entry.value for entry in bundle.entries}
            self._hierarchy.set_chunk(bundle.domain, entries)
        return self.merge_all()

    def merge_all(self) -> MergedRuntime:
        """Merge all populated domains into a unified MergedRuntime."""
        domains: Dict[str, MergedKnowledge] = {}
        all_domains = set()
        for level in SnapshotHierarchy.ORDER:
            all_domains.update(self._hierarchy._layers[level].keys())

        for domain in all_domains:
            domains[domain] = self.merge_domain(domain)

        self._merged = MergedRuntime(
            domains=domains,
            version=self.version,
        )
        return self._merged

    def get_merged(self) -> Optional[MergedRuntime]:
        """Get the previously computed merged runtime."""
        return self._merged

    def reset(self) -> "KnowledgeMerger":
        """Reset the merger state."""
        self._hierarchy = SnapshotHierarchy()
        self._merged = None
        return self

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "knowledge_merger",
            "version": self.version,
            "hierarchy": self._hierarchy.manifest(),
            "has_merged_runtime": self._merged is not None,
            "enabled": True,
        }


__all__ = [
    "MergeStrategy",
    "DOMAIN_STRATEGIES",
    "MergedKnowledge",
    "MergedRuntime",
    "KnowledgeMerger",
]