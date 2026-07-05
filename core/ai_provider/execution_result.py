from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .contracts import ProviderResponse
from .execution_context import ExecutionContext


@dataclass
class ExecutionResult:
    response: ProviderResponse
    context: Optional[ExecutionContext] = None
    attempts: int = 1
    provider_name: Optional[str] = None
    retry_count: int = 0
    timed_out: bool = False
    cancelled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return self.response.text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response.to_dict(),
            "context": self.context.to_dict() if self.context else None,
            "attempts": self.attempts,
            "provider_name": self.provider_name or self.response.provider,
            "retry_count": self.retry_count,
            "timed_out": self.timed_out,
            "cancelled": self.cancelled,
            "metadata": dict(self.metadata),
        }
