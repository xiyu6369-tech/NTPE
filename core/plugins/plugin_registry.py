from __future__ import annotations

from collections import defaultdict
from typing import Any

from .plugin_base import PluginBase
from .plugin_context import PluginContext


class PluginRegistry:
    def __init__(self, context: PluginContext):
        self.context = context
        self._plugins: dict[str, PluginBase] = {}
        self._stages: dict[str, list[PluginBase]] = defaultdict(list)

    def register(self, plugin: PluginBase) -> None:
        if not plugin.enabled:
            return

        if plugin.name in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin.name}")

        plugin.setup(self.context)

        self._plugins[plugin.name] = plugin
        self._stages[plugin.stage].append(plugin)
        self._stages[plugin.stage].sort(key=lambda item: item.priority)

    def get(self, name: str) -> PluginBase | None:
        return self._plugins.get(name)

    def list_plugins(self) -> list[str]:
        return sorted(self._plugins.keys())

    def list_stages(self) -> list[str]:
        return sorted(self._stages.keys())

    def run_stage(self, stage: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = dict(payload)

        for plugin in self._stages.get(stage, []):
            result = plugin.run(result, self.context)

            if not isinstance(result, dict):
                raise TypeError(
                    f"Plugin {plugin.name} returned {type(result)}, expected dict"
                )

        return result