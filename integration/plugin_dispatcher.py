"""Plugin command dispatcher for NTPE Stage-08.3."""
from __future__ import annotations

from typing import Any

from .plugin_context import PluginIntegrationContext
from .plugin_models import PluginCommand, PluginIntegrationResult
from .plugin_registry import PluginIntegrationRegistry


class PluginDispatcher:
    version = "0.8.3"

    def __init__(self, registry: PluginIntegrationRegistry) -> None:
        self.registry = registry

    def dispatch(self, command: PluginCommand, context: PluginIntegrationContext | None = None) -> PluginIntegrationResult:
        try:
            plugin = self.registry.require(command.plugin_name)
            method_name = self._resolve_method(plugin, command.action)
            method = getattr(plugin, method_name)
            ctx = context or PluginIntegrationContext(operation=f"plugin.{command.action}", plugin_name=command.plugin_name, session_id=command.session_id)
            value = self._call(method, ctx, command.payload)
            self.registry.mark(command.plugin_name, self._status_for(command.action))
            return PluginIntegrationResult.success(command.plugin_name, command.action, value=value, method=method_name, correlation_id=ctx.correlation_id)
        except Exception as exc:
            return PluginIntegrationResult.failure(command.plugin_name, command.action, str(exc), correlation_id=getattr(context, "correlation_id", command.correlation_id))

    @staticmethod
    def _resolve_method(plugin: Any, action: str) -> str:
        aliases = {
            "load": ["load"],
            "initialize": ["initialize", "init"],
            "execute": ["execute", "run"],
            "run": ["run", "execute"],
            "unload": ["unload", "shutdown"],
            "descriptor": ["descriptor"],
        }
        for candidate in aliases.get(action, [action]):
            if hasattr(plugin, candidate):
                return candidate
        raise AttributeError(f"plugin action unavailable: {action}")

    @staticmethod
    def _call(method: Any, context: PluginIntegrationContext, payload: dict) -> Any:
        try:
            return method(context.to_sdk_context(), **payload)
        except TypeError:
            try:
                return method(**payload)
            except TypeError:
                return method()

    @staticmethod
    def _status_for(action: str) -> str:
        return {"load": "loaded", "initialize": "initialized", "execute": "executed", "run": "executed", "unload": "unloaded"}.get(action, "completed")
