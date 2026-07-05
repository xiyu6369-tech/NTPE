from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from .contracts import ProviderRequest
from .provider_pool import ProviderPool, ProviderPoolEntry
from .provider_score import ProviderScore

ROUTE_HEALTH_BASED = "health_based"
ROUTE_WEIGHTED = "weighted"
ROUTE_PRIORITY = "priority"
ROUTE_COST_AWARE = "cost_aware"
ROUTE_LATENCY_AWARE = "latency_aware"
ROUTE_CAPABILITY_AWARE = "capability_aware"
ROUTE_BALANCED = "balanced"


@dataclass
class RoutingPolicy:
    """Deterministic provider routing policy.

    Stage-14.4 supports multiple routing modes while preserving a stable default
    order. The default balanced mode combines health, capability, weight,
    priority, latency, failure rate, and cost signals.
    """

    mode: str = ROUTE_BALANCED
    required_capabilities: List[str] = field(default_factory=list)
    fallback_order: List[str] = field(default_factory=list)
    max_candidates: Optional[int] = None

    def score_provider(self, provider, pool_entry: ProviderPoolEntry, request: ProviderRequest, statistics: Optional[Dict[str, Dict[str, float]]] = None) -> ProviderScore:
        name = pool_entry.name
        stats = (statistics or {}).get(name, {})
        healthy = True
        try:
            healthy = bool(provider.health().get("healthy", True))
        except Exception:
            healthy = False
        capability_match = self._capability_match(provider, request)
        estimated_cost = 0.0
        try:
            usage = getattr(request, "metadata", {}).get("estimated_usage")
            if usage is not None:
                estimated_cost = provider.estimate_cost(usage, request.model).total_cost
        except Exception:
            estimated_cost = 0.0
        return ProviderScore(
            provider=name,
            healthy=healthy,
            weight=pool_entry.weight,
            priority=pool_entry.priority,
            latency_ms=stats.get("average_latency_ms"),
            estimated_cost=estimated_cost,
            capability_match=capability_match,
            failure_count=int(stats.get("failure_count", 0)),
            success_count=int(stats.get("success_count", 0)),
            metadata={"mode": self.mode},
        )

    def order(self, registry, pool: ProviderPool, request: ProviderRequest, statistics: Optional[Dict[str, Dict[str, float]]] = None) -> List[str]:
        candidates: List[tuple[ProviderPoolEntry, ProviderScore]] = []
        for entry in pool.entries(enabled_only=True):
            if not registry.has(entry.name):
                continue
            provider = registry.get(entry.name)
            score = self.score_provider(provider, entry, request, statistics)
            if score.healthy and score.capability_match:
                candidates.append((entry, score))
        if not candidates:
            return []
        if self.fallback_order:
            ranked = sorted(candidates, key=lambda pair: self._fallback_index(pair[0].name, pair[0].priority))
        elif self.mode == ROUTE_PRIORITY:
            ranked = sorted(candidates, key=lambda pair: (pair[0].priority, pair[0].name))
        elif self.mode == ROUTE_WEIGHTED:
            ranked = sorted(candidates, key=lambda pair: (-pair[0].weight, pair[0].priority, pair[0].name))
        elif self.mode == ROUTE_COST_AWARE:
            ranked = sorted(candidates, key=lambda pair: (pair[1].estimated_cost, pair[0].priority, pair[0].name))
        elif self.mode == ROUTE_LATENCY_AWARE:
            ranked = sorted(candidates, key=lambda pair: (pair[1].latency_ms if pair[1].latency_ms is not None else 10**9, pair[0].priority, pair[0].name))
        else:
            ranked = sorted(candidates, key=lambda pair: (-pair[1].value(), pair[0].priority, pair[0].name))
        names = [entry.name for entry, _ in ranked]
        if self.max_candidates is not None:
            names = names[: self.max_candidates]
        return names

    def _capability_match(self, provider, request: ProviderRequest) -> bool:
        cap = provider.detect_capabilities()
        if request.stream and not cap.streaming:
            return False
        for item in self.required_capabilities:
            if not bool(getattr(cap, item, False)):
                if not bool(cap.custom.get(item, False)):
                    return False
        return True

    def _fallback_index(self, name: str, priority: int) -> tuple[int, int, str]:
        try:
            return (self.fallback_order.index(name), priority, name)
        except ValueError:
            return (10**6, priority, name)

    def to_dict(self) -> Dict[str, object]:
        return {
            "mode": self.mode,
            "required_capabilities": list(self.required_capabilities),
            "fallback_order": list(self.fallback_order),
            "max_candidates": self.max_candidates,
        }
