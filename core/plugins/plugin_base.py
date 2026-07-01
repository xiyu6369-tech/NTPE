from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .plugin_context import PluginContext


class PluginBase(ABC):
    name: str = "base"
    stage: str = "base"
    enabled: bool = True
    priority: int = 100

    def setup(self, context: PluginContext) -> None:
        pass

    @abstractmethod
    def run(self, payload: dict[str, Any], context: PluginContext) -> dict[str, Any]:
        raise NotImplementedError