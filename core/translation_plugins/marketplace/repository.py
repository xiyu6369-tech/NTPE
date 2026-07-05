from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .manifest import MarketplacePluginManifest


@dataclass
class PluginRepository:
    root: Path
    plugins: dict[str, MarketplacePluginManifest] = field(default_factory=dict)

    @property
    def index_path(self) -> Path:
        return self.root / "marketplace_index.json"

    @classmethod
    def load(cls, root: str | Path) -> "PluginRepository":
        repo = cls(root=Path(root))
        repo.root.mkdir(parents=True, exist_ok=True)
        if repo.index_path.exists():
            data = json.loads(repo.index_path.read_text(encoding="utf-8"))
            for item in data.get("plugins", []):
                manifest = MarketplacePluginManifest.from_dict(item)
                repo.plugins[manifest.plugin_id] = manifest
        return repo

    def add(self, manifest: MarketplacePluginManifest, replace: bool = False) -> dict[str, Any]:
        if manifest.plugin_id in self.plugins and not replace:
            return {"status": "failed", "error": f"plugin already exists: {manifest.plugin_id}"}
        self.plugins[manifest.plugin_id] = manifest
        self.save()
        return {"status": "success", "plugin_id": manifest.plugin_id}

    def remove(self, plugin_id: str) -> dict[str, Any]:
        if plugin_id not in self.plugins:
            return {"status": "failed", "error": f"plugin not found: {plugin_id}"}
        del self.plugins[plugin_id]
        self.save()
        return {"status": "success", "plugin_id": plugin_id}

    def list(self) -> list[dict[str, Any]]:
        return [manifest.to_dict() for manifest in self.plugins.values()]

    def save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {"schema": "ntpe.plugin.marketplace.v1", "plugins": self.list()}
        self.index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
