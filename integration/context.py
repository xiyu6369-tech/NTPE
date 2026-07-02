"""Shared context object for Stage-08 integration operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict
import uuid


@dataclass
class IntegrationContext:
    operation: str
    correlation_id: str = field(default_factory=lambda: f"int-{uuid.uuid4().hex[:12]}")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def child(self, operation: str, **metadata: Any) -> "IntegrationContext":
        merged = dict(self.metadata)
        merged.update(metadata)
        merged["parent_correlation_id"] = self.correlation_id
        return IntegrationContext(operation=operation, metadata=merged)

    def to_dict(self) -> Dict[str, Any]:
        return {"operation": self.operation, "correlation_id": self.correlation_id, "metadata": dict(self.metadata)}
