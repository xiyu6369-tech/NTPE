"""Workflow context for NTPE Stage-09.0."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class WorkflowContext:
    session_id: str = "default"
    source: str = "workflow"
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> "WorkflowContext":
        self.state[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return {"session_id": self.session_id, "source": self.source, "metadata": dict(self.metadata), "state": dict(self.state)}
