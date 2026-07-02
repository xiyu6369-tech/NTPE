"""Component registry for NTPE Stage-08 integration."""
from __future__ import annotations

from typing import Dict, Iterable, Optional

from .contracts import IntegrationComponent


class IntegrationRegistry:
    """Small stable registry used by Stage-08 to connect Runtime/CLI/SDK/Plugin."""

    def __init__(self) -> None:
        self._components: Dict[str, IntegrationComponent] = {}

    def register(self, component: IntegrationComponent) -> IntegrationComponent:
        if not component.name:
            raise ValueError("integration component name is required")
        self._components[component.name] = component
        return component

    def register_instance(self, name: str, kind: str, instance: object, *, version: str = "1.0", metadata: Optional[dict] = None) -> IntegrationComponent:
        return self.register(IntegrationComponent(name=name, kind=kind, version=version, instance=instance, metadata=dict(metadata or {})))

    def get(self, name: str) -> Optional[IntegrationComponent]:
        return self._components.get(name)

    def require(self, name: str) -> IntegrationComponent:
        component = self.get(name)
        if component is None:
            raise KeyError(f"integration component not registered: {name}")
        return component

    def names(self) -> list[str]:
        return list(self._components.keys())

    def components(self) -> Iterable[IntegrationComponent]:
        return tuple(self._components.values())

    def manifest(self) -> dict:
        return {"count": len(self._components), "components": [item.to_dict() for item in self.components()]}
