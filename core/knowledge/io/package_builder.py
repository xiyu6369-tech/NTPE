"""Foundation-08.8 Knowledge package builder."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..contracts import KnowledgeItem, KnowledgeQuery, KnowledgeRepository, KnowledgeSnapshot
from ..snapshot import KnowledgeSnapshotSerializer
from .validation import SUPPORTED_PACKAGE_VERSION, SUPPORTED_SCHEMA


class KnowledgePackageBuilder:
    """Build portable packages from repositories and snapshots."""

    version = SUPPORTED_PACKAGE_VERSION

    def __init__(self, repository: Optional[KnowledgeRepository] = None, metadata: Optional[Dict[str, Any]] = None):
        self.repository = repository
        self.metadata = dict(metadata or {})
        self.serializer = KnowledgeSnapshotSerializer()

    def build(
        self,
        name: str = "knowledge-package",
        domains: Optional[Iterable[str]] = None,
        snapshots: Optional[Iterable[KnowledgeSnapshot | Dict[str, Any]]] = None,
        include_items: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        domains_list = list(domains or [])
        items: List[Dict[str, Any]] = []
        if include_items and self.repository is not None:
            if domains_list:
                for domain in domains_list:
                    items.extend(item.to_dict() for item in self.repository.query(KnowledgeQuery(domain=domain)))
            else:
                items.extend(item.to_dict() for item in self.repository.query(KnowledgeQuery()))

        snapshot_payloads = [self.serializer.to_dict(snapshot) for snapshot in snapshots or []]
        merged_metadata = {**self.metadata, **dict(metadata or {})}
        manifest = {
            "name": name,
            "schema": SUPPORTED_SCHEMA,
            "version": self.version,
            "domains": domains_list or sorted({item.get("domain", "general") for item in items}),
            "item_count": len(items),
            "snapshot_count": len(snapshot_payloads),
            "metadata": merged_metadata,
        }
        return {"manifest": manifest, "items": items, "snapshots": snapshot_payloads}

    def build_from_snapshot(self, snapshot: KnowledgeSnapshot | Dict[str, Any], name: str = "snapshot-package") -> Dict[str, Any]:
        payload = self.serializer.to_dict(snapshot)
        manifest = {
            "name": name,
            "schema": SUPPORTED_SCHEMA,
            "version": self.version,
            "domains": sorted({item.get("domain", "general") for item in payload.get("items", [])}),
            "item_count": len(payload.get("items", [])),
            "snapshot_count": 1,
            "metadata": {**self.metadata, "source": "snapshot"},
        }
        return {"manifest": manifest, "items": list(payload.get("items", [])), "snapshots": [payload]}


__all__ = ["KnowledgePackageBuilder"]
