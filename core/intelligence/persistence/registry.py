"""Foundation-07.4 Intelligence persistence registry."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ..persistence_contract import IntelligencePersistenceContract
from .json_store import JsonIntelligenceStore
from .sqlite_store import SQLiteIntelligenceStore

StoreFactory = Callable[..., IntelligencePersistenceContract]


class IntelligencePersistenceRegistry:
    """Registry for selecting persistence implementations without binding runtime code."""

    version = "foundation-07.4"

    def __init__(self) -> None:
        self._factories: Dict[str, StoreFactory] = {}
        self.register("json", JsonIntelligenceStore)
        self.register("sqlite", SQLiteIntelligenceStore)

    def register(self, name: str, factory: StoreFactory) -> None:
        if not name:
            raise ValueError("store name is required")
        self._factories[name.lower()] = factory

    def names(self) -> list[str]:
        return sorted(self._factories.keys())

    def create(self, name: str = "json", **kwargs: Any) -> IntelligencePersistenceContract:
        key = (name or "json").lower()
        if key not in self._factories:
            raise KeyError(f"unknown intelligence persistence store: {name}")
        return self._factories[key](**kwargs)

    def get(self, name: str) -> Optional[StoreFactory]:
        return self._factories.get((name or "").lower())


_default_registry = IntelligencePersistenceRegistry()


def get_default_persistence_registry() -> IntelligencePersistenceRegistry:
    return _default_registry
