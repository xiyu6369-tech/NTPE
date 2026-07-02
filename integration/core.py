"""NTPE Stage-08.0 Integration Core.

The core is intentionally thin: it coordinates already-existing Runtime, CLI,
SDK and Plugin surfaces without taking ownership of their contracts.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .contracts import IntegrationComponent, IntegrationResult
from .context import IntegrationContext
from .manifest import build_integration_manifest
from .registry import IntegrationRegistry


class IntegrationCore:
    version = "0.8.0"

    def __init__(self, *, registry: Optional[IntegrationRegistry] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.registry = registry or IntegrationRegistry()
        self.metadata = dict(metadata or {})
        self.events: list[dict] = []

    def register_component(self, name: str, kind: str, instance: Any = None, *, version: str = "1.0", metadata: Optional[Dict[str, Any]] = None) -> IntegrationComponent:
        component = IntegrationComponent(name=name, kind=kind, version=version, instance=instance, metadata=dict(metadata or {}))
        self.registry.register(component)
        self._emit("component_registered", {"component": component.to_dict()})
        return component

    def bridge_sdk(self, sdk_client: Any, *, name: str = "sdk") -> IntegrationComponent:
        return self.register_component(name, "sdk", sdk_client, version=str(getattr(sdk_client, "version", "1.0")))

    def bridge_runtime(self, runtime: Any, *, name: str = "runtime") -> IntegrationComponent:
        return self.register_component(name, "runtime", runtime, version=str(getattr(runtime, "version", "1.0")))

    def bridge_plugin_manager(self, plugin_manager: Any, *, name: str = "plugin_manager") -> IntegrationComponent:
        return self.register_component(name, "plugin", plugin_manager, version=str(getattr(plugin_manager, "version", "1.0")))

    def invoke(self, component_name: str, method_name: str, *args: Any, **kwargs: Any) -> IntegrationResult:
        context = IntegrationContext(operation=f"{component_name}.{method_name}")
        try:
            component = self.registry.require(component_name)
            target = component.instance
            if target is None:
                raise RuntimeError(f"component has no instance: {component_name}")
            method = getattr(target, method_name)
            value = method(*args, **kwargs)
            result = IntegrationResult.success(context.operation, component=component_name, data={"value": value, "context": context.to_dict()})
            self._emit("invoke_completed", result.to_dict())
            return result
        except Exception as exc:
            result = IntegrationResult.failure(context.operation, str(exc), component=component_name, data={"context": context.to_dict()})
            self._emit("invoke_failed", result.to_dict())
            return result

    def health(self) -> IntegrationResult:
        required = {"sdk", "runtime", "plugin_manager"}
        registered = set(self.registry.names())
        data = {"registered": sorted(registered), "missing_optional": sorted(required - registered), "registry": self.registry.manifest()}
        return IntegrationResult.success("integration.health", data=data)

    def manifest(self) -> Dict[str, Any]:
        manifest = build_integration_manifest(self.metadata)
        manifest["registry"] = self.registry.manifest()
        manifest["events"] = list(self.events)
        return manifest

    def _emit(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self.events.append({"type": event_type, "payload": dict(payload or {})})


def create_integration_core(**kwargs: Any) -> IntegrationCore:
    return IntegrationCore(**kwargs)
