from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PluginPackagePublisher:
    """Publishes built plugin package metadata to a local repository index.

    Stage-13 intentionally implements local publishing only. Remote publishing,
    signatures, and network transport are reserved for later stages so the
    marketplace remains deterministic and testable without external services.
    """

    repository_root: Path

    @classmethod
    def create(cls, repository_root: str | Path) -> "PluginPackagePublisher":
        return cls(repository_root=Path(repository_root))

    @property
    def index_path(self) -> Path:
        return self.repository_root / "published_plugins.json"

    def load_index(self) -> dict[str, Any]:
        self.repository_root.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            return {"schema": "ntpe.plugin.publisher.v1", "packages": []}
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def save_index(self, index: dict[str, Any]) -> None:
        self.repository_root.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    def publish_metadata(self, metadata_path: str | Path, replace: bool = False) -> dict[str, Any]:
        source = Path(metadata_path)
        if not source.exists():
            return {"status": "failed", "error": "metadata file not found", "metadata_path": str(source)}
        metadata = json.loads(source.read_text(encoding="utf-8"))
        plugin_id = str(metadata.get("plugin_id", ""))
        version = str(metadata.get("version", ""))
        if not plugin_id or not version:
            return {"status": "failed", "error": "metadata missing plugin_id or version"}

        index = self.load_index()
        packages = list(index.get("packages", []))
        exists = [item for item in packages if item.get("plugin_id") == plugin_id and item.get("version") == version]
        if exists and not replace:
            return {"status": "failed", "plugin_id": plugin_id, "version": version, "error": "package already published"}
        packages = [item for item in packages if not (item.get("plugin_id") == plugin_id and item.get("version") == version)]
        packages.append(metadata)
        packages.sort(key=lambda item: (item.get("plugin_id", ""), item.get("version", "")))
        index["packages"] = packages
        self.save_index(index)
        return {"status": "success", "plugin_id": plugin_id, "version": version, "package_count": len(packages)}

    def list_published(self) -> dict[str, Any]:
        index = self.load_index()
        packages = list(index.get("packages", []))
        return {"status": "success", "package_count": len(packages), "packages": packages}
