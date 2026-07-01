"""Foundation-07.3 Intelligence persistence contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Dict, List, Optional


class IntelligencePersistenceContract(ABC):
    """Storage-neutral contract for future JSON/SQLite/Redis persistence."""

    @abstractmethod
    def save_snapshot(self, scope_key: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def load_snapshot(self, scope_key: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_scope_keys(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def delete_snapshot(self, scope_key: str) -> bool:
        raise NotImplementedError


class InMemoryIntelligencePersistence(IntelligencePersistenceContract):
    """Small default persistence adapter used by tests and runtime-safe callers."""

    def __init__(self) -> None:
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    def save_snapshot(self, scope_key: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        self._snapshots[scope_key] = deepcopy(snapshot)
        return deepcopy(self._snapshots[scope_key])

    def load_snapshot(self, scope_key: str) -> Optional[Dict[str, Any]]:
        snapshot = self._snapshots.get(scope_key)
        return deepcopy(snapshot) if snapshot is not None else None

    def list_scope_keys(self) -> List[str]:
        return list(self._snapshots.keys())

    def delete_snapshot(self, scope_key: str) -> bool:
        return self._snapshots.pop(scope_key, None) is not None
