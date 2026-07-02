"""Extension dispatcher for NTPE Stage-08.4."""
from __future__ import annotations

from typing import Any

from .extension_context import ExtensionContext
from .extension_models import ExtensionCommand, ExtensionResult
from .extension_registry import ExtensionRegistry


class ExtensionDispatcher:
    version = "0.8.4"

    def __init__(self, registry: ExtensionRegistry) -> None:
        self.registry = registry

    def dispatch(self, command: ExtensionCommand, context: ExtensionContext | None = None) -> ExtensionResult:
        try:
            extension = self.registry.require(command.extension_name)
            method_name = self._resolve_method(extension, command.action)
            method = getattr(extension, method_name)
            ctx = context or ExtensionContext(operation=f"extension.{command.action}", extension_name=command.extension_name, session_id=command.session_id)
            value = self._call(method, ctx, command.payload)
            self.registry.mark(command.extension_name, self._status_for(command.action))
            return ExtensionResult.success(command.extension_name, command.action, value=value, method=method_name, correlation_id=ctx.correlation_id)
        except Exception as exc:
            return ExtensionResult.failure(command.extension_name, command.action, str(exc), correlation_id=getattr(context, "correlation_id", command.correlation_id))

    @staticmethod
    def _resolve_method(extension: Any, action: str) -> str:
        aliases = {
            "load": ["load"],
            "initialize": ["initialize", "init"],
            "enable": ["enable"],
            "disable": ["disable"],
            "execute": ["execute", "run"],
            "run": ["run", "execute"],
            "unload": ["unload", "shutdown"],
            "manifest": ["get_manifest", "manifest_dict"],
        }
        for candidate in aliases.get(action, [action]):
            if hasattr(extension, candidate):
                return candidate
        raise AttributeError(f"extension action unavailable: {action}")

    @staticmethod
    def _call(method: Any, context: ExtensionContext, payload: dict) -> Any:
        try:
            return method(context, **payload)
        except TypeError:
            try:
                return method(**payload)
            except TypeError:
                return method()

    @staticmethod
    def _status_for(action: str) -> str:
        return {
            "load": "loaded",
            "initialize": "initialized",
            "enable": "enabled",
            "disable": "disabled",
            "execute": "executed",
            "run": "executed",
            "unload": "unloaded",
        }.get(action, "completed")
