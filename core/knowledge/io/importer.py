"""Foundation-08.8 Knowledge importer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from ..contracts import KnowledgeItem, KnowledgeQuery, KnowledgeRepository, KnowledgeSnapshot
from .package_reader import KnowledgePackageReader
from .validation import KnowledgePackageValidator


class KnowledgeImporter:
    """Import portable packages into a KnowledgeRepository."""

    version = "foundation-08.8"

    def __init__(self, repository: KnowledgeRepository, validator: Optional[KnowledgePackageValidator] = None):
        self.repository = repository
        self.validator = validator or KnowledgePackageValidator()
        self.reader = KnowledgePackageReader(self.validator)
        self.last_result: Dict[str, Any] = {}

    def import_package(self, package: Dict[str, Any], merge: bool = True) -> Dict[str, Any]:
        payload = self.reader.read_dict(package)
        imported = 0
        skipped = 0
        if not merge:
            # Contract-safe repositories do not expose clear(); delete by current query.
            for item in list(self.repository.query(KnowledgeQuery())):
                self.repository.delete(item.key, item.domain)
        for item_payload in payload.get("items", []):
            item = KnowledgeItem.from_dict(item_payload)
            if merge or self.repository.get(item.key, item.domain) is None:
                self.repository.put(item)
                imported += 1
            else:
                skipped += 1
        result = {
            "imported": imported,
            "skipped": skipped,
            "snapshot_count": len(payload.get("snapshots", [])),
            "manifest": payload.get("manifest", {}),
        }
        self.last_result = result
        return result

    def import_json(self, path: str | Path, merge: bool = True) -> Dict[str, Any]:
        return self.import_package(self.reader.read_json(path), merge=merge)

    def import_zip(self, path: str | Path, merge: bool = True) -> Dict[str, Any]:
        return self.import_package(self.reader.read_zip(path), merge=merge)

    def import_snapshot(self, snapshot: KnowledgeSnapshot | Dict[str, Any], merge: bool = True) -> Dict[str, Any]:
        if isinstance(snapshot, dict):
            snapshot = KnowledgeSnapshot.from_dict(snapshot)
        package = {
            "manifest": {
                "name": snapshot.name,
                "schema": "ntpe.knowledge.package.v1",
                "version": self.version,
                "domains": sorted({item.domain for item in snapshot.items}),
                "item_count": len(snapshot.items),
                "snapshot_count": 1,
                "metadata": {"source": "snapshot_import"},
            },
            "items": [item.to_dict() for item in snapshot.items],
            "snapshots": [snapshot.to_dict()],
        }
        return self.import_package(package, merge=merge)


__all__ = ["KnowledgeImporter"]
