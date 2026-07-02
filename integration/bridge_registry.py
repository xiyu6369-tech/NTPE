"""SDK-CLI bridge endpoint registry for NTPE Stage-08.2."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .bridge_models import BridgeEndpoint


class BridgeRegistry:
    version = "0.8.2"

    def __init__(self) -> None:
        self._items: Dict[str, BridgeEndpoint] = {}

    def register(self, name: str, kind: str, instance: Any, *, version: str = "1.0", metadata: Optional[Dict[str, Any]] = None) -> BridgeEndpoint:
        endpoint = BridgeEndpoint(name=name, kind=kind, instance=instance, version=version, metadata=dict(metadata or {}))
        self._items[name] = endpoint
        return endpoint

    def get(self, name: str) -> Optional[BridgeEndpoint]:
        return self._items.get(name)

    def require(self, name: str) -> BridgeEndpoint:
        endpoint = self.get(name)
        if endpoint is None:
            raise KeyError(f"bridge endpoint not registered: {name}")
        return endpoint

    def names(self) -> List[str]:
        return sorted(self._items)

    def by_kind(self, kind: str) -> List[BridgeEndpoint]:
        return [item for item in self._items.values() if item.kind == kind]

    def manifest(self) -> Dict[str, Any]:
        return {"version": self.version, "count": len(self._items), "names": self.names(), "endpoints": [item.to_dict() for item in self._items.values()]}
