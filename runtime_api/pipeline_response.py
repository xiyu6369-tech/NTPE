"""Runtime Pipeline API response helpers for NTPE 1.0 Beta Stage-11.4."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable

from .runtime_pipeline import RuntimePipeline

RUNTIME_PIPELINE_RESPONSE_VERSION = "1.0.0-beta.11.4"
RUNTIME_PIPELINE_RESPONSE_STAGE = "11.4"


@dataclass(frozen=True)
class RuntimePipelineListResponse:
    """Serializable pipeline-list response."""

    pipelines: tuple[RuntimePipeline, ...] = field(default_factory=tuple)

    version = RUNTIME_PIPELINE_RESPONSE_VERSION
    stage = RUNTIME_PIPELINE_RESPONSE_STAGE

    @classmethod
    def from_pipelines(cls, pipelines: Iterable[RuntimePipeline]) -> "RuntimePipelineListResponse":
        return cls(pipelines=tuple(pipelines))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "pipelines": [pipeline.to_dict() for pipeline in self.pipelines],
            "count": len(self.pipelines),
        }
