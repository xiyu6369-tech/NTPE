"""Runtime context objects for Stage-08.1."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid


@dataclass
class RuntimeContext:
    operation: str
    runtime_id: Optional[str] = None
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    correlation_id: str = field(default_factory=lambda: f"rtctx-{uuid.uuid4().hex[:12]}")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def child(self, operation: str, **metadata: Any) -> "RuntimeContext":
        merged = dict(self.metadata)
        merged.update(metadata)
        merged["parent_correlation_id"] = self.correlation_id
        return RuntimeContext(
            operation=operation,
            runtime_id=self.runtime_id,
            session_id=self.session_id,
            job_id=self.job_id,
            metadata=merged,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "runtime_id": self.runtime_id,
            "session_id": self.session_id,
            "job_id": self.job_id,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
        }
