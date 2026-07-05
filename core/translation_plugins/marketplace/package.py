from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .manifest import MarketplacePluginManifest


@dataclass(frozen=True)
class MarketplacePluginPackage:
    manifest: MarketplacePluginManifest
    source_path: Path

    @classmethod
    def load(cls, path: str | Path) -> "MarketplacePluginPackage":
        source = Path(path)
        manifest_path = source / "plugin_manifest.json" if source.is_dir() else source
        data: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
        return cls(manifest=MarketplacePluginManifest.from_dict(data), source_path=source)

    def validate(self, ntpe_version: str = "1.2.0") -> dict[str, Any]:
        result = self.manifest.validate(ntpe_version=ntpe_version)
        exists = self.source_path.exists()
        errors = list(result.get("errors", []))
        if not exists:
            errors.append("source_path does not exist")
        return {
            "status": "success" if not errors else "failed",
            "plugin_id": self.manifest.plugin_id,
            "errors": errors,
            "source_path": str(self.source_path),
        }
