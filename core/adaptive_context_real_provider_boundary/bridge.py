from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan

SafeProviderResult = Mapping[str, object]
RealInvoker = Callable[[Mapping[str, object], ProviderAttemptPlan, str, str], Mapping[str, object]]
_SAFE_RESULT_KEYS = frozenset({
    "status", "error", "http_status", "status_code", "provider_model",
    "fallback_used", "estimated_input_tokens", "estimated_output_tokens",
    "actual_input_tokens", "actual_output_tokens", "usage_source",
})


class ProviderInvocationBridge(Protocol):
    provenance: str

    def invoke(
        self, payload: Mapping[str, object], plan: ProviderAttemptPlan, *,
        provider_url: str, api_key: str,
    ) -> SafeProviderResult: ...


def sanitize_provider_result(result: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in result.items() if key in _SAFE_RESULT_KEYS}


@dataclass
class FakeProviderInvocationBridge:
    outcomes: tuple[str, ...] = ("success",)
    provenance: str = "fake"

    def __post_init__(self) -> None:
        self.calls = 0

    def invoke(
        self, payload: Mapping[str, object], plan: ProviderAttemptPlan, *,
        provider_url: str, api_key: str,
    ) -> SafeProviderResult:
        if api_key:
            raise ValueError("fake-bridge-must-not-receive-api-key")
        index = min(self.calls, len(self.outcomes) - 1)
        outcome = self.outcomes[index] if self.outcomes else "success"
        self.calls += 1
        base: dict[str, object] = {
            "provider_model": plan.model,
            "fallback_used": plan.fallback_used,
            "actual_input_tokens": plan.estimated_input_tokens,
            "actual_output_tokens": plan.estimated_output_tokens,
            "usage_source": "fake",
        }
        if outcome == "success":
            return {**base, "status": "success"}
        if outcome == "timeout":
            return {**base, "status": "failed", "error": "provider request timed out"}
        if outcome == "503":
            return {**base, "status": "failed", "error": "service unavailable", "http_status": 503}
        return {**base, "status": "failed", "error": "fake provider failure"}


@dataclass(frozen=True)
class CallableRealProviderInvocationBridge:
    invoker: RealInvoker
    provenance: str = "real"

    def invoke(
        self, payload: Mapping[str, object], plan: ProviderAttemptPlan, *,
        provider_url: str, api_key: str,
    ) -> SafeProviderResult:
        if not api_key:
            raise ValueError("real-provider-environment-credential-required")
        return sanitize_provider_result(self.invoker(payload, plan, provider_url, api_key))
