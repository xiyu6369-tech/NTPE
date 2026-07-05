from __future__ import annotations

from dataclasses import dataclass

from .manifest import MarketplacePluginManifest


@dataclass
class DependencyResolver:
    installed: dict[str, MarketplacePluginManifest]

    def missing_dependencies(self, manifest: MarketplacePluginManifest) -> list[str]:
        return [dep for dep in manifest.dependencies if dep not in self.installed]

    def can_install(self, manifest: MarketplacePluginManifest) -> dict[str, object]:
        missing = self.missing_dependencies(manifest)
        return {
            "status": "success" if not missing else "failed",
            "plugin_id": manifest.plugin_id,
            "missing_dependencies": missing,
        }
