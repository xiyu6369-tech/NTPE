from __future__ import annotations

from typing import Any

from .plugin import TranslationPlugin, TranslationPluginProtocol


class TranslationPluginRegistry:
    """Stable plugin registry for NTPE 1.2 Professional.

    The registry is intentionally small and deterministic: registration is by
    kind/name, replacements are opt-in, and list order is insertion order.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, TranslationPluginProtocol] = {}

    def register(self, plugin: TranslationPluginProtocol, replace: bool = False) -> TranslationPluginProtocol:
        key = self._key(plugin.kind, plugin.name)
        if key in self._plugins and not replace:
            raise ValueError(f"plugin already registered: {key}")
        self._plugins[key] = plugin
        return plugin

    def register_default(self, kind: str, name: str = "default", replace: bool = False, **metadata: Any) -> TranslationPlugin:
        plugin = TranslationPlugin(name=name, kind=kind, metadata=metadata)
        self.register(plugin, replace=replace)
        return plugin

    def get(self, kind: str, name: str = "default") -> TranslationPluginProtocol | None:
        return self._plugins.get(self._key(kind, name))

    def require(self, kind: str, name: str = "default") -> TranslationPluginProtocol:
        plugin = self.get(kind, name)
        if plugin is None:
            raise KeyError(f"missing plugin: {kind}:{name}")
        return plugin

    def list(self, kind: str | None = None) -> list[dict[str, Any]]:
        plugins = self._plugins.values()
        if kind is not None:
            plugins = [plugin for plugin in plugins if plugin.kind == kind]
        return [plugin.to_dict() if hasattr(plugin, "to_dict") else self._fallback(plugin) for plugin in plugins]

    def keys(self) -> list[str]:
        return list(self._plugins.keys())

    @staticmethod
    def _key(kind: str, name: str) -> str:
        return f"{kind}:{name}"

    @staticmethod
    def _fallback(plugin: TranslationPluginProtocol) -> dict[str, Any]:
        return {
            "name": plugin.name,
            "kind": plugin.kind,
            "version": getattr(plugin, "version", "unknown"),
            "enabled": bool(getattr(plugin, "enabled", True)),
            "metadata": {},
        }
