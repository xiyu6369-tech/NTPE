from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .contracts import ProviderResponse
from .execution_result import ExecutionResult


@dataclass
class ProviderAttempt:
    provider: str
    success: bool
    error: Optional[str] = None
    latency_ms: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "success": self.success,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "retry_count": self.retry_count,
            "metadata": dict(self.metadata),
        }


@dataclass
class OrchestrationResult:
    response: ProviderResponse
    selected_provider: str
    attempts: List[ProviderAttempt] = field(default_factory=list)
    execution_result: Optional[ExecutionResult] = None
    fallback_used: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return bool(self.response.success)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_provider": self.selected_provider,
            "success": self.success,
            "fallback_used": self.fallback_used,
            "response": self.response.to_dict(),
            "attempts": [item.to_dict() for item in self.attempts],
            "execution_result": self.execution_result.to_dict() if self.execution_result else None,
            "metadata": dict(self.metadata),
        }
