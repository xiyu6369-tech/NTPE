from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.adaptive_context_real_provider_boundary import (
    CallableRealProviderInvocationBridge,
    FakeProviderInvocationBridge,
    ProviderInvocationBridge,
)
from core.adaptive_context_real_provider_boundary.bridge import RealInvoker, SafeProviderResult


class AuthorizedProviderTransport(ProviderInvocationBridge, Protocol):
    """Shared Stage 10.4 invocation contract for fake and real transports."""


@dataclass
class FakeAuthorizedProviderTransport:
    outcomes: tuple[str, ...] = ("success",)
    provenance: str = "fake"

    def __post_init__(self) -> None:
        self._bridge = FakeProviderInvocationBridge(self.outcomes)

    @property
    def calls(self) -> int:
        return self._bridge.calls

    def invoke(
        self, payload: Mapping[str, object], plan: ProviderAttemptPlan, *,
        provider_url: str, api_key: str,
    ) -> SafeProviderResult:
        return self._bridge.invoke(
            payload, plan, provider_url=provider_url, api_key=api_key,
        )


@dataclass(frozen=True)
class CallableRealAuthorizedProviderTransport:
    invoker: RealInvoker
    provenance: str = "real"

    def invoke(
        self, payload: Mapping[str, object], plan: ProviderAttemptPlan, *,
        provider_url: str, api_key: str,
    ) -> SafeProviderResult:
        bridge = CallableRealProviderInvocationBridge(self.invoker)
        return bridge.invoke(
            payload, plan, provider_url=provider_url, api_key=api_key,
        )
