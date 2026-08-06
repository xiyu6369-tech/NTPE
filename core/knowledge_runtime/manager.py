"""RM-6.1.1 Knowledge Runtime Manager — domain-aware orchestration.

No provider imports. No benchmark hooks. No feedback integration.
Coordinates Loader → Resolver → Bundle → Snapshot pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .errors import KnowledgeManagerError
from .loader import KnowledgeLoader
from .models import KnowledgeBundle, KnowledgeEntry, KnowledgeSnapshot
from .resolver import KnowledgeResolver
from .snapshot import KnowledgeSnapshotStore


class KnowledgeRuntimeManager:
    """Orchestrate the end-to-end knowledge runtime pipeline.

    Coordinates loader, resolver, and snapshot store in a
    purely offline, provider-free architecture skeleton.
    """

    version = "rm-6.1.1"

    def __init__(self, source: Optional[Dict[str, Any]] = None):
        self.loader = KnowledgeLoader(source)
        self.resolver = KnowledgeResolver()
        self.snapshots = KnowledgeSnapshotStore()

    def load_and_resolve(self, domain: str) -> List[KnowledgeEntry]:
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
            "resolver": self.resolver.manifest(),
            "snapshots": self.snapshots.manifest(),
            "enabled": True,
        }


__all__ = ["KnowledgeRuntimeManager"]