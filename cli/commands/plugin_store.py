from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_PLUGINS: Dict[str, Dict[str, Any]] = {
    "context": {
        "name": "context",
        "version": "foundation-v1.0",
        "kind": "context",
        "enabled": True,
        "source": "built-in",
        "description": "Context pipeline plugin",
    },
    "prompt": {
        "name": "prompt",
        "version": "foundation-v1.0",
        "kind": "prompt",
        "enabled": True,
        "source": "built-in",
        "description": "Prompt pipeline plugin",
    },
    "narrative": {
        "name": "narrative",
        "version": "foundation-v1.0",
        "kind": "narrative",
        "enabled": True,
        "source": "built-in",
        "description": "Narrative pipeline plugin",
    },
    "quality": {
        "name": "quality",
        "version": "foundation-v1.0",
        "kind": "quality",
        "enabled": True,
        "source": "built-in",
        "description": "Quality pipeline plugin",
    },
}


@dataclass
class PluginValidation:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid, "errors": list(self.errors), "warnings": list(self.warnings)}


class CLIPluginStore:
    """Small CLI-facing plugin registry.

    It intentionally does not replace Foundation Plugin System internals. It
    provides a stable product-layer registry used by the CLI for listing,
    toggling, importing and validating plugin metadata.
    """

    def __init__(self, root: Path, plugin_dir: str = ".ntpe_plugins") -> None:
        self.root = Path(root)
        self.plugin_dir = self.root / plugin_dir
        self.registry_path = self.plugin_dir / "plugin_registry.json"
        self.packages_dir = self.plugin_dir / "packages"

    def ensure(self) -> Dict[str, Any]:
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            data = {"version": "1.0-beta-stage-06.7", "plugins": dict(DEFAULT_PLUGINS)}
            self._write(data)
            return data
        data = self.load()
        changed = False
        plugins = data.setdefault("plugins", {})
        for name, meta in DEFAULT_PLUGINS.items():
            if name not in plugins:
                plugins[name] = dict(meta)
                changed = True
        if changed:
            self._write(data)
        return data

    def load(self) -> Dict[str, Any]:
        if not self.registry_path.exists():
            return self.ensure()
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"version": "1.0-beta-stage-06.7", "plugins": {}}
        data.setdefault("version", "1.0-beta-stage-06.7")
        data.setdefault("plugins", {})
        return data

    def _write(self, data: Dict[str, Any]) -> None:
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def list(self, enabled: Optional[bool] = None) -> List[Dict[str, Any]]:
        data = self.ensure()
        items = [dict(plugin) for plugin in data.get("plugins", {}).values()]
        if enabled is not None:
            items = [plugin for plugin in items if bool(plugin.get("enabled", False)) is enabled]
        return sorted(items, key=lambda item: str(item.get("name", "")))

    def info(self, name: str) -> Optional[Dict[str, Any]]:
        data = self.ensure()
        plugin = data.get("plugins", {}).get(name)
        return dict(plugin) if plugin else None

    def enable(self, name: str, value: bool = True) -> Dict[str, Any]:
        data = self.ensure()
        plugins = data.setdefault("plugins", {})
        if name not in plugins:
            raise KeyError(f"plugin not found: {name}")
        plugins[name]["enabled"] = bool(value)
        self._write(data)
        return dict(plugins[name])

    def disable(self, name: str) -> Dict[str, Any]:
        return self.enable(name, False)

    def uninstall(self, name: str) -> Dict[str, Any]:
        data = self.ensure()
        plugins = data.setdefault("plugins", {})
        if name not in plugins:
            raise KeyError(f"plugin not found: {name}")
        removed = dict(plugins.pop(name))
        self._write(data)
        package_path = self.packages_dir / name
        if package_path.exists():
            if package_path.is_dir():
                shutil.rmtree(package_path)
            else:
                package_path.unlink()
        return removed

    def install(self, package: Path, replace: bool = False) -> Dict[str, Any]:
        package = Path(package)
        if not package.exists():
            raise FileNotFoundError(f"plugin package not found: {package}")
        meta = self._read_package_metadata(package)
        name = str(meta.get("name") or package.stem).strip()
        if not name:
            raise ValueError("plugin name is required")
        meta.setdefault("name", name)
        meta.setdefault("version", "0.0.0")
        meta.setdefault("kind", "custom")
        meta.setdefault("enabled", True)
        meta.setdefault("source", str(package))
        meta.setdefault("description", "Imported plugin")

        data = self.ensure()
        plugins = data.setdefault("plugins", {})
        if name in plugins and not replace:
            raise FileExistsError(f"plugin already exists: {name}")
        plugins[name] = dict(meta)
        self._write(data)
        return dict(plugins[name])

    def validate(self, name: Optional[str] = None) -> PluginValidation:
        data = self.ensure()
        errors: List[str] = []
        warnings: List[str] = []
        plugins = data.get("plugins", {})
        names: Iterable[str]
        if name:
            names = [name]
            if name not in plugins:
                errors.append(f"plugin not found: {name}")
        else:
            names = plugins.keys()
        seen = set()
        for plugin_name in names:
            plugin = plugins.get(plugin_name)
            if not plugin:
                continue
            actual = plugin.get("name")
            if not actual:
                errors.append(f"plugin missing name: {plugin_name}")
            if actual in seen:
                errors.append(f"duplicate plugin name: {actual}")
            seen.add(actual)
            if "enabled" not in plugin:
                warnings.append(f"plugin missing enabled flag: {actual}")
            if not plugin.get("kind"):
                warnings.append(f"plugin missing kind: {actual}")
        return PluginValidation(valid=not errors, errors=errors, warnings=warnings)

    def manifest(self) -> Dict[str, Any]:
        data = self.ensure()
        plugins = data.get("plugins", {})
        return {
            "registry": str(self.registry_path),
            "plugin_dir": str(self.plugin_dir),
            "count": len(plugins),
            "enabled": sum(1 for plugin in plugins.values() if plugin.get("enabled")),
        }

    def _read_package_metadata(self, package: Path) -> Dict[str, Any]:
        if package.is_dir():
            for candidate in ("ntpe_plugin.json", "plugin.json", "manifest.json"):
                path = package / candidate
                if path.exists():
                    return json.loads(path.read_text(encoding="utf-8"))
            return {"name": package.name, "source": str(package), "kind": "directory"}
        if package.suffix.lower() == ".json":
            data = json.loads(package.read_text(encoding="utf-8"))
            if "plugin" in data and isinstance(data["plugin"], dict):
                data = data["plugin"]
            data.setdefault("source", str(package))
            return data
        return {"name": package.stem, "source": str(package), "kind": package.suffix.lstrip(".") or "file"}
