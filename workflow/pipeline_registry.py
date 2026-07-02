"""Pipeline registry for NTPE Stage-09.2."""
from __future__ import annotations
from typing import Dict, Iterable
from .pipeline_models import PipelineDefinition, PipelineStatus

class PipelineRegistry:
    def __init__(self) -> None:
        self._items: Dict[str, PipelineDefinition] = {}

    def register(self, pipeline: PipelineDefinition) -> PipelineDefinition:
        pipeline.status = PipelineStatus.REGISTERED
        self._items[pipeline.name] = pipeline
        return pipeline

    def get(self, name: str) -> PipelineDefinition:
        if name not in self._items:
            raise KeyError(f"pipeline not registered: {name}")
        return self._items[name]

    def names(self) -> list[str]:
        return sorted(self._items.keys())

    def all(self) -> Iterable[PipelineDefinition]:
        return tuple(self._items.values())

    def manifest(self) -> dict:
        return {"count": len(self._items), "pipelines": self.names()}
