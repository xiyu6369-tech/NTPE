# =====================================================
# NTPE 1.2 Professional
# Stage-16.7 Intelligence Runtime Integration
# =====================================================

from __future__ import annotations

from typing import Any, Dict, Iterable


class IntelligenceRuntimeRegistry:
    """Compatibility-safe registry for runtime intelligence engines."""

    def __init__(self) -> None:
        self._engines: Dict[str, Any] = {}

    def register(self, name: str, engine: Any) -> None:
        if not name:
            raise ValueError("engine name must not be empty")
        self._engines[name] = engine

    def get(self, name: str, default: Any = None) -> Any:
        return self._engines.get(name, default)

    def names(self) -> Iterable[str]:
        return tuple(self._engines.keys())

    def to_dict(self) -> Dict[str, str]:
        return {name: engine.__class__.__name__ for name, engine in self._engines.items()}
