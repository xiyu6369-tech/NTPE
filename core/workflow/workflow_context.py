# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping


@dataclass
class WorkflowContext:
    source_text: str
    source_language: str = "auto"
    target_language: str = "zh-TW"
    workflow_id: str = "workflow"
    provider: str | None = None
    strategy: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def require_text(self) -> None:
        if not self.source_text or not self.source_text.strip():
            from .workflow_exceptions import WorkflowInputError
            raise WorkflowInputError("source_text must not be empty")

    def record(self, step: str, **payload: Any) -> None:
        item = {"step": step}
        item.update(payload)
        self.history.append(item)

    def update_artifacts(self, values: Mapping[str, Any]) -> None:
        self.artifacts.update(dict(values))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "provider": self.provider,
            "strategy": self.strategy,
            "metadata": dict(self.metadata),
            "artifacts": dict(self.artifacts),
            "history": list(self.history),
        }
