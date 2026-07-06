from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable


class ConfigRegistry:
    """In-memory additive registry for config providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, values: Dict[str, Any]) -> None:
        if not name:
            raise ValueError("provider name is required")
        if not isinstance(values, dict):
            raise TypeError("provider values must be a dictionary")
        self._providers[name] = deepcopy(values)

    def get(self, name: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return deepcopy(self._providers.get(name, default or {}))

    def names(self) -> list[str]:
        return sorted(self._providers)

    def merge(self) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for name in self.names():
            merged = _deep_merge(merged, self._providers[name])
        return merged


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
