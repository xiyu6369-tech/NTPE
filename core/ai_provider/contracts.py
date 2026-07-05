from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, List, Optional


@dataclass(frozen=True)
class ProviderCapability:
    """Declarative provider capability descriptor.

    The class is intentionally dependency-free and serialisable so it can be
    consumed by CLI, runtime manifests, tests, and future provider plugins.
    """

    completion: bool = True
    streaming: bool = False
    model_discovery: bool = False
    token_usage: bool = False
    cost_statistics: bool = False
    health_check: bool = True
    rate_limit: bool = True
    retry: bool = True
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "completion": self.completion,
            "streaming": self.streaming,
            "model_discovery": self.model_discovery,
            "token_usage": self.token_usage,
            "cost_statistics": self.cost_statistics,
            "health_check": self.health_check,
            "rate_limit": self.rate_limit,
            "retry": self.retry,
            "custom": dict(self.custom),
        }


@dataclass(frozen=True)
class ModelInfo:
    id: str
    provider: str
    context_window: Optional[int] = None
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    supports_streaming: bool = False
    capabilities: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "context_window": self.context_window,
            "input_cost_per_1k": self.input_cost_per_1k,
            "output_cost_per_1k": self.output_cost_per_1k,
            "supports_streaming": self.supports_streaming,
            "capabilities": dict(self.capabilities),
        }


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self) -> None:
        if not self.total_tokens:
            self.total_tokens = self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> Dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class CostStatistics:
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    currency: str = "USD"

    def __post_init__(self) -> None:
        if not self.total_cost:
            self.total_cost = self.input_cost + self.output_cost

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "total_cost": self.total_cost,
            "currency": self.currency,
        }


@dataclass
class ProviderRequest:
    prompt: str
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    stream: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@dataclass
class ProviderResponse:
    text: str
    provider: str
    model: Optional[str] = None
    success: bool = True
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    usage: TokenUsage = field(default_factory=TokenUsage)
    cost: CostStatistics = field(default_factory=CostStatistics)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "provider": self.provider,
            "model": self.model,
            "success": self.success,
            "latency_ms": self.latency_ms,
            "metadata": dict(self.metadata),
            "usage": self.usage.to_dict(),
            "cost": self.cost.to_dict(),
        }


@dataclass
class ProviderStreamChunk:
    text: str
    provider: str
    model: Optional[str] = None
    index: int = 0
    done: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderError(Exception):
    message: str
    provider: Optional[str] = None
    retryable: bool = True
    status_code: Optional[int] = None

    def __str__(self) -> str:
        return self.message


class AIProvider:
    """Stable provider interface for NTPE 1.2 Professional.

    Existing Stage-03 callers only need ``complete`` and ``health``; the new
    methods are additive and have safe defaults to preserve backward
    compatibility with frozen NTPE 1.0/1.1 surfaces.
    """

    name = "base"
    provider_type = "custom"
    default_model: Optional[str] = None
    capabilities = ProviderCapability()

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError

    def stream(self, request: ProviderRequest) -> Iterator[ProviderStreamChunk]:
        response = self.complete(request)
        yield ProviderStreamChunk(
            text=response.text,
            provider=response.provider,
            model=response.model,
            index=0,
            done=True,
            metadata=response.metadata,
        )

    def discover_models(self) -> List[ModelInfo]:
        if self.default_model:
            return [ModelInfo(id=self.default_model, provider=self.name)]
        return []

    def detect_capabilities(self) -> ProviderCapability:
        return self.capabilities

    def estimate_cost(self, usage: TokenUsage, model: Optional[str] = None) -> CostStatistics:
        models = {m.id: m for m in self.discover_models()}
        info = models.get(model or self.default_model or "")
        if not info:
            return CostStatistics()
        return CostStatistics(
            input_cost=(usage.prompt_tokens / 1000.0) * info.input_cost_per_1k,
            output_cost=(usage.completion_tokens / 1000.0) * info.output_cost_per_1k,
        )

    def health(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "provider_type": self.provider_type,
            "healthy": True,
            "capabilities": self.detect_capabilities().to_dict(),
            "models": [m.to_dict() for m in self.discover_models()],
        }


class MockProvider(AIProvider):
    def __init__(
        self,
        name: str = "mock",
        response_text: str = "mock translation",
        fail_times: int = 0,
        retryable: bool = True,
        models: Optional[Iterable[ModelInfo]] = None,
        capabilities: Optional[ProviderCapability] = None,
    ):
        self.name = name
        self.provider_type = "mock"
        self.response_text = response_text
        self.fail_times = fail_times
        self.retryable = retryable
        self.calls = 0
        self._models = list(models or [ModelInfo(id="mock-model", provider=name, supports_streaming=True)])
        self.default_model = self._models[0].id if self._models else None
        self.capabilities = capabilities or ProviderCapability(
            streaming=True,
            model_discovery=True,
            token_usage=True,
            cost_statistics=True,
        )

    def discover_models(self) -> List[ModelInfo]:
        return [ModelInfo(**{**m.to_dict(), "provider": self.name}) for m in self._models]

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.calls += 1
        start = time.time()
        if self.calls <= self.fail_times:
            raise ProviderError(f"{self.name} simulated failure", self.name, self.retryable)
        text = self.response_text
        if "{prompt}" in text:
            text = text.replace("{prompt}", request.prompt)
        usage = TokenUsage(prompt_tokens=max(1, len(request.prompt.split())), completion_tokens=max(1, len(text.split())))
        cost = self.estimate_cost(usage, request.model or self.default_model)
        return ProviderResponse(
            text=text,
            provider=self.name,
            model=request.model or self.default_model,
            latency_ms=(time.time() - start) * 1000,
            metadata={"calls": self.calls},
            usage=usage,
            cost=cost,
        )
