from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .contracts import ProviderRequest
from .load_balancer import ProviderLoadBalancer
from .provider_pool import ProviderPool
from .registry import ProviderRegistry, build_standard_provider_registry
from .routing_policy import RoutingPolicy


@dataclass
class MultiProviderOrchestrator:
    """High-level multi-provider orchestration facade."""

    registry: ProviderRegistry = field(default_factory=build_standard_provider_registry)
    load_balancer: Optional[ProviderLoadBalancer] = None

    def __post_init__(self) -> None:
        if self.load_balancer is None:
            self.load_balancer = ProviderLoadBalancer(self.registry)

    def complete(self, request: ProviderRequest):
        return self.load_balancer.execute(request).response

    def execute(self, request: ProviderRequest):
        return self.load_balancer.execute(request)

    def translate(self, text: str, **kwargs) -> str:
        return self.complete(ProviderRequest(prompt=text, **kwargs)).text

    def configure_pool(self, pool: ProviderPool) -> None:
        self.load_balancer.pool = pool

    def configure_routing(self, routing_policy: RoutingPolicy) -> None:
        self.load_balancer.routing_policy = routing_policy

    def manifest(self) -> Dict[str, object]:
        return {
            "component": "multi_provider_orchestrator",
            "stage": "NTPE 1.2 Professional Stage-14.4",
            "registry": self.registry.manifest(),
            "load_balancer": self.load_balancer.manifest(),
        }
