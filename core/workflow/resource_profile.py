# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class ResourceProfile:
    provider: str = "default"
    model: str = "default"
    max_tokens_per_request: int = 4096
    tokens_per_minute: int = 60000
    requests_per_minute: int = 60
    cost_per_1k_tokens: float = 0.0
    worker_weight: float = 1.0
    cache_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def estimate_cost(self, token_count: int) -> float:
        token_count = max(0, int(token_count))
        return (token_count / 1000.0) * max(0.0, float(self.cost_per_1k_tokens))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "max_tokens_per_request": self.max_tokens_per_request,
            "tokens_per_minute": self.tokens_per_minute,
            "requests_per_minute": self.requests_per_minute,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "worker_weight": self.worker_weight,
            "cache_enabled": self.cache_enabled,
            "metadata": dict(self.metadata),
        }
