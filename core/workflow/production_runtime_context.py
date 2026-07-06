# =====================================================
# NTPE 1.2 Professional
# Stage-17.7 Production Runtime Integration
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass
class ProductionRuntimeContext:
    source_text: str
    source_language: str = "auto"
    target_language: str = "zh-TW"
    runtime_id: str = "production-runtime"
    workflow_id: str = "workflow"
    job_id: str | None = None
    provider: str | None = None
    strategy: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_text or not self.source_text.strip():
            from .production_runtime_exceptions import ProductionRuntimeInputError
            raise ProductionRuntimeInputError("source_text must not be empty")

    def update_artifacts(self, values: Mapping[str, Any]) -> None:
        self.artifacts.update(dict(values))

    def to_workflow_context(self):
        from .workflow_context import WorkflowContext
        return WorkflowContext(
            source_text=self.source_text,
            source_language=self.source_language,
            target_language=self.target_language,
            workflow_id=self.workflow_id,
            provider=self.provider,
            strategy=self.strategy,
            metadata=dict(self.metadata),
            artifacts=dict(self.artifacts),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "workflow_id": self.workflow_id,
            "job_id": self.job_id,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "provider": self.provider,
            "strategy": self.strategy,
            "metadata": dict(self.metadata),
            "artifacts": dict(self.artifacts),
        }
