"""Shared SDK-CLI bridge context for NTPE Stage-08.2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class BridgeContext:
    operation: str
    surface: str = "bridge"
    session_id: Optional[str] = None
    runtime_id: Optional[str] = None
    configuration: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: f"bridge-{uuid4().hex[:12]}")

    def child(self, operation: str, **metadata: Any) -> "BridgeContext":
        merged = dict(self.metadata)
        merged.update(metadata)
        merged["parent_correlation_id"] = self.correlation_id
        return BridgeContext(
            operation=operation,
            surface=self.surface,
            session_id=self.session_id,
            runtime_id=self.runtime_id,
            configuration=dict(self.configuration),
            metadata=merged,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "surface": self.surface,
            "session_id": self.session_id,
            "runtime_id": self.runtime_id,
            "configuration": dict(self.configuration),
            "metadata": dict(self.metadata),
            "correlation_id": self.correlation_id,
        }
