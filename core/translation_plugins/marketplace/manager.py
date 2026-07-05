from __future__ import annotations

from pathlib import Path
from typing import Any

from .installer import PluginInstaller
from .repository import PluginRepository


class PluginMarketplaceManager:
    """Stage-11 marketplace interface for installable NTPE plugins.

    This layer manages plugin packages and repository metadata. It does not
    execute plugins directly; execution remains owned by TranslationPluginRuntime.
    """

    version = "1.2-professional-stage-11"
    compatibility_floor = "1.1-lts-stable"

    def __init__(self, root: str | Path, ntpe_version: str = "1.2.0") -> None:
        self.root = Path(root)
        self.ntpe_version = ntpe_version
        self.repository = PluginRepository.load(self.root / "plugins" / "marketplace")
        self.installer = PluginInstaller(root=self.root, repository=self.repository, ntpe_version=ntpe_version)

    def install(self, package_path: str | Path, replace: bool = False) -> dict[str, Any]:
        return self.installer.install(package_path, replace=replace)

    def uninstall(self, plugin_id: str) -> dict[str, Any]:
        return self.installer.uninstall(plugin_id)

    def list_plugins(self) -> dict[str, Any]:
        return {
            "status": "success",
            "version": self.version,
            "plugin_count": len(self.repository.plugins),
            "plugins": self.repository.list(),
        }

    def validate(self) -> dict[str, Any]:
        invalid = []
        for manifest in self.repository.plugins.values():
            result = manifest.validate(ntpe_version=self.ntpe_version)
            if result["status"] != "success":
                invalid.append(result)
        return {
            "status": "success" if not invalid else "failed",
            "version": self.version,
            "compatibility_floor": self.compatibility_floor,
            "plugin_count": len(self.repository.plugins),
            "invalid": invalid,
        }
