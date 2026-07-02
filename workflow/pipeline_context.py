"""Pipeline context for NTPE Stage-09.2."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class PipelineContext:
    pipeline_id: str = "default"
    source: str = "pipeline"
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> "PipelineContext":
        self.state[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "source": self.source,
            "metadata": dict(self.metadata),
            "state": dict(self.state),
        }
