from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .dependency import DependencyResolver
from .package import MarketplacePluginPackage
from .repository import PluginRepository


@dataclass
class PluginInstaller:
    root: Path
    repository: PluginRepository
    ntpe_version: str = "1.2.0"

    @property
    def installed_dir(self) -> Path:
        return self.root / "plugins" / "installed"

    def install(self, package_path: str | Path, replace: bool = False) -> dict[str, Any]:
        package = MarketplacePluginPackage.load(package_path)
        validation = package.validate(ntpe_version=self.ntpe_version)
        if validation["status"] != "success":
            return validation
        resolver = DependencyResolver(installed=dict(self.repository.plugins))
        dependency_check = resolver.can_install(package.manifest)
        if dependency_check["status"] != "success":
            return dependency_check
        target = self.installed_dir / package.manifest.plugin_id
        if target.exists() and not replace:
            return {"status": "failed", "plugin_id": package.manifest.plugin_id, "error": "plugin already installed"}
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        (target / "plugin_manifest.json").write_text(
            json.dumps(package.manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.repository.add(package.manifest, replace=True)
        return {"status": "success", "plugin_id": package.manifest.plugin_id, "install_path": str(target)}

    def uninstall(self, plugin_id: str) -> dict[str, Any]:
        target = self.installed_dir / plugin_id
        if target.exists():
            shutil.rmtree(target)
        repo_result = self.repository.remove(plugin_id) if plugin_id in self.repository.plugins else {"status": "success", "plugin_id": plugin_id}
        return {"status": "success", "plugin_id": plugin_id, "repository": repo_result}
