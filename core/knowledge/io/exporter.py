"""Foundation-08.8 Knowledge exporter."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from ..contracts import KnowledgeRepository, KnowledgeSnapshot
from .package_builder import KnowledgePackageBuilder
from .validation import KnowledgePackageValidator


class KnowledgeExporter:
    """Export repository knowledge as JSON or ZIP packages."""

    version = "foundation-08.8"

    def __init__(self, repository: Optional[KnowledgeRepository] = None, metadata: Optional[Dict[str, Any]] = None):
        self.repository = repository
        self.builder = KnowledgePackageBuilder(repository=repository, metadata=metadata)
        self.validator = KnowledgePackageValidator()

    def package(
        self,
        name: str = "knowledge-package",
        domains: Optional[Iterable[str]] = None,
        snapshots: Optional[Iterable[KnowledgeSnapshot | Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = self.builder.build(name=name, domains=domains, snapshots=snapshots, metadata=metadata)
        self.validator.ensure_valid(payload)
        return payload

    def export_json(self, path: str | Path, package: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Path:
        payload = package or self.package(**kwargs)
        self.validator.ensure_valid(payload)
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def export_zip(self, path: str | Path, package: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Path:
        payload = package or self.package(**kwargs)
        self.validator.ensure_valid(payload)
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("knowledge_package.json", json.dumps(payload, ensure_ascii=False, indent=2))
            archive.writestr("manifest.json", json.dumps(payload.get("manifest", {}), ensure_ascii=False, indent=2))
        return output_path

    def export_snapshot_package(self, snapshot: KnowledgeSnapshot | Dict[str, Any], path: str | Path) -> Path:
        payload = self.builder.build_from_snapshot(snapshot)
        suffix = Path(path).suffix.lower()
        if suffix == ".zip":
            return self.export_zip(path, package=payload)
        return self.export_json(path, package=payload)


__all__ = ["KnowledgeExporter"]
