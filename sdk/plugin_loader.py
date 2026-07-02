"""Stage-07.7 SDK Plugin loader."""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union

from .plugin import SDKPlugin
from .plugin_manifest import PluginManifest


class SDKPluginLoader:
    def from_class(self, plugin_cls: Type[SDKPlugin], manifest: Optional[PluginManifest] = None, **metadata: Any) -> SDKPlugin:
        return plugin_cls(manifest=manifest, **metadata)

    def from_manifest(self, manifest: Union[PluginManifest, Dict[str, Any]]) -> SDKPlugin:
        plugin_manifest = manifest if isinstance(manifest, PluginManifest) else PluginManifest.from_dict(dict(manifest))
        if plugin_manifest.entrypoint:
            module_name, _, attr = plugin_manifest.entrypoint.partition(":")
            module = importlib.import_module(module_name)
            plugin_cls = getattr(module, attr or "Plugin")
            return self.from_class(plugin_cls, plugin_manifest)
        return SDKPlugin(manifest=plugin_manifest)

    def from_file(self, path: Union[str, Path]) -> SDKPlugin:
        import json

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.from_manifest(data)
