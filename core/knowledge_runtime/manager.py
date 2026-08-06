"""RM-6.1.2 Knowledge Runtime Manager — domain-aware orchestration with Merge Engine.

No provider imports. No benchmark hooks. No feedback integration.
Coordinates Loader → Snapshot → Merger → Resolver pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .errors import KnowledgeManagerError
from .loader import KnowledgeLoader
from .merger import KnowledgeMerger, MergedRuntime
from .models import KnowledgeBundle, KnowledgeEntry, KnowledgeSnapshot
from .resolver import KnowledgeResolver
from .snapshot import KnowledgeSnapshotStore


class KnowledgeRuntimeManager:
    """Orchestrate the end-to-end knowledge runtime pipeline.

    Coordinates loader, merger, resolver, and snapshot store in a
    purely offline, provider-free architecture skeleton.

    Pipeline: Loader → Snapshot → Merger → Resolver
    """

    version = "rm-6.1.2"

    def __init__(self, source: Optional[Dict[str, Any]] = None):
        self.loader = KnowledgeLoader(source)
        self.merger = KnowledgeMerger()
        self.resolver = KnowledgeResolver()
        self.snapshots = KnowledgeSnapshotStore()
        self._merged_runtime: Optional[MergedRuntime] = None

    def load_and_resolve(self, domain: str) -> List[KnowledgeEntry]:
        """Load domain and resolve through merger (backward compatible)."""
        prototypes = self.loader.load_domain(domain)
        self.resolver.prototypes = prototypes
        return self.resolver.resolve_all()

    def build_bundle(
        self,
        bundle_id: str,
        domain: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeBundle:
        entries = self.load_and_resolve(domain)
        return KnowledgeBundle(
            id=bundle_id,
            entries=entries,
            domain=domain,
            metadata=dict(metadata or {}),
        )

    def load_character(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBundle:
        return self.loader.load_character_bundle(metadata)

    def load_glossary(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBundle:
        return self.loader.load_glossary_bundle(metadata)

    def load_scene(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBundle:
        return self.loader.load_scene_bundle(metadata)

    def load_narrative(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBundle:
        return self.loader.load_narrative_bundle(metadata)

    def load_style(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBundle:
        return self.loader.load_style_bundle(metadata)

    def load_all(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, KnowledgeBundle]:
        return self.loader.load_all_bundles(metadata)

    def build_merged_runtime(
        self,
        bundles: Optional[List[KnowledgeBundle]] = None,
        snapshots: Optional[List[KnowledgeSnapshot]] = None,
    ) -> MergedRuntime:
        """Build the merged runtime from bundles and/or snapshots.

        This is the core RM-6.1.2 pipeline step: Loader → Snapshot → Merger.
        The Resolver will then query ONLY this merged runtime.
        """
        self.merger.reset()

        # Apply bundles at chunk level (highest priority)
        if bundles:
            for bundle in bundles:
                entries = {entry.key: entry.value for entry in bundle.entries}
                self.merger.set_chunk(bundle.domain, entries)

        # Apply snapshots at chunk level
        if snapshots:
            for snapshot in snapshots:
                for bundle in snapshot.bundles:
                    entries = {entry.key: entry.value for entry in bundle.entries}
                    self.merger.set_chunk(bundle.domain, entries)

        # Build merged runtime
        self._merged_runtime = self.merger.merge_all()

        # Update resolver to use merged runtime
        self._update_resolver_from_merged()

        return self._merged_runtime

    def _update_resolver_from_merged(self) -> None:
        """Update resolver prototypes from merged runtime."""
        if self._merged_runtime is None:
            return

        prototypes = []
        for domain, merged_knowledge in self._merged_runtime.domains.items():
            for key, value in merged_knowledge.entries.items():
                from .models import KnowledgePrototype
                prototypes.append(
                    KnowledgePrototype(
                        key=key,
                        domain=domain,
                        metadata={"value": value},
                    )
                )
        self.resolver.prototypes = prototypes
        self.resolver.index_prototypes()

    def get_merged_runtime(self) -> Optional[MergedRuntime]:
        """Get the current merged runtime."""
        return self._merged_runtime

    def resolve_merged(self, key: str, domain: str = "general") -> KnowledgeEntry:
        """Resolve a key from the merged runtime only.

        This is the RM-6.1.2 contract: Resolver queries merged runtime exclusively.
        """
        if self._merged_runtime is None:
            raise KnowledgeManagerError("No merged runtime built. Call build_merged_runtime() first.")

        value = self._merged_runtime.resolve(key, domain)
        if value is None:
            raise KnowledgeManagerError(f"Cannot resolve {domain}:{key} from merged runtime")

        return KnowledgeEntry(
            key=key,
            value=value,
            domain=domain,
            source="merged_runtime",
            version=self.version,
        )

    def resolve_all_merged(self, domain: str) -> List[KnowledgeEntry]:
        """Resolve all keys for a domain from the merged runtime."""
        if self._merged_runtime is None:
            raise KnowledgeManagerError("No merged runtime built. Call build_merged_runtime() first.")

        merged_domain = self._merged_runtime.get_domain(domain)
        if merged_domain is None:
            return []

        return [
            KnowledgeEntry(
                key=key,
                value=value,
                domain=domain,
                source="merged_runtime",
                version=self.version,
            )
            for key, value in merged_domain.entries.items()
        ]

    def capture(
        self,
        snapshot_id: str,
        bundle_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeSnapshot:
        bundles = []
        for bid in bundle_ids or []:
            try:
                stored = self.snapshots.retrieve(bid)
                bundles.extend(stored.bundles)
            except KnowledgeManagerError:
                pass
        snapshot = self.snapshots.build(
            snapshot_id, bundles=bundles, metadata=metadata
        )
        return snapshot

    def restore(self, snapshot_id: str) -> List[KnowledgeEntry]:
        return self.snapshots.restore_entries(snapshot_id)

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "knowledge_runtime_manager",
            "version": self.version,
            "loader": self.loader.manifest(),
            "merger": self.merger.manifest(),
            "resolver": self.resolver.manifest(),
            "snapshots": self.snapshots.manifest(),
            "has_merged_runtime": self._merged_runtime is not None,
            "enabled": True,
        }


__all__ = ["KnowledgeRuntimeManager"]