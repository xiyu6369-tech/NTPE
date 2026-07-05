from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .contracts import AIProvider, ModelInfo, ProviderCapability, ProviderRequest, ProviderResponse, TokenUsage


@dataclass
class ProviderAdapterConfig:
    name: str
    provider_type: str
    default_model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    models: List[ModelInfo] = field(default_factory=list)
    capabilities: ProviderCapability = field(default_factory=ProviderCapability)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProviderAdapter(AIProvider):
    """Config-backed adapter base for hosted, local, and custom providers.

    Stage-14 deliberately keeps network transport outside this class so tests and
    project validation remain deterministic. Real HTTP clients can subclass this
    adapter without changing the registry, manager, or runtime bridge contracts.
    """

    def __init__(self, config: ProviderAdapterConfig):
        self.config = config
        self.name = config.name
        self.provider_type = config.provider_type
        self.default_model = config.default_model
        self.capabilities = config.capabilities

    def discover_models(self) -> List[ModelInfo]:
        return [ModelInfo(**{**m.to_dict(), "provider": self.name}) for m in self.config.models]

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError(f"{self.name} requires a concrete transport implementation")

    def health(self) -> Dict[str, Any]:
        payload = super().health()
        payload.update(
            {
                "configured": bool(self.config.api_key or self.config.base_url or self.provider_type in {"ollama", "custom"}),
                "base_url": self.config.base_url,
                "metadata": dict(self.config.metadata),
            }
        )
        return payload


class StaticProviderAdapter(ProviderAdapter):
    """Deterministic adapter used for offline validation and custom plugins."""

    def __init__(self, config: ProviderAdapterConfig, response_template: str = "{prompt}"):
        super().__init__(config)
        self.response_template = response_template

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        text = self.response_template.replace("{prompt}", request.prompt)
        usage = TokenUsage(prompt_tokens=max(1, len(request.prompt.split())), completion_tokens=max(1, len(text.split())))
        return ProviderResponse(
            text=text,
            provider=self.name,
            model=request.model or self.default_model,
            usage=usage,
            cost=self.estimate_cost(usage, request.model or self.default_model),
            metadata={"adapter": "static", "provider_type": self.provider_type},
        )


def _models(provider: str, rows: Iterable[Dict[str, Any]]) -> List[ModelInfo]:
    return [ModelInfo(provider=provider, **row) for row in rows]


def build_standard_provider_configs() -> Dict[str, ProviderAdapterConfig]:
    streaming_completion = ProviderCapability(
        streaming=True,
        model_discovery=True,
        token_usage=True,
        cost_statistics=True,
    )
    local_completion = ProviderCapability(
        streaming=True,
        model_discovery=True,
        token_usage=False,
        cost_statistics=False,
    )
    custom_completion = ProviderCapability(
        streaming=True,
        model_discovery=True,
        token_usage=True,
        cost_statistics=True,
        custom={"user_defined_transport": True},
    )

    return {
        "nvidia": ProviderAdapterConfig(
            name="nvidia",
            provider_type="nvidia",
            default_model="meta/llama-3.3-70b-instruct",
            base_url="https://integrate.api.nvidia.com/v1",
            capabilities=streaming_completion,
            models=_models(
                "nvidia",
                [
                    {"id": "meta/llama-3.3-70b-instruct", "context_window": 131072, "supports_streaming": True},
                ],
            ),
        ),
        "openai": ProviderAdapterConfig(
            name="openai",
            provider_type="openai",
            default_model="gpt-4.1-mini",
            base_url="https://api.openai.com/v1",
            capabilities=streaming_completion,
            models=_models("openai", [{"id": "gpt-4.1-mini", "supports_streaming": True}]),
        ),
        "gemini": ProviderAdapterConfig(
            name="gemini",
            provider_type="gemini",
            default_model="gemini-2.5-flash",
            base_url="https://generativelanguage.googleapis.com/v1beta",
            capabilities=streaming_completion,
            models=_models("gemini", [{"id": "gemini-2.5-flash", "supports_streaming": True}]),
        ),
        "anthropic": ProviderAdapterConfig(
            name="anthropic",
            provider_type="anthropic",
            default_model="claude-3-5-sonnet-latest",
            base_url="https://api.anthropic.com/v1",
            capabilities=streaming_completion,
            models=_models("anthropic", [{"id": "claude-3-5-sonnet-latest", "supports_streaming": True}]),
        ),
        "ollama": ProviderAdapterConfig(
            name="ollama",
            provider_type="ollama",
            default_model="llama3.1",
            base_url="http://localhost:11434/api",
            capabilities=local_completion,
            models=_models("ollama", [{"id": "llama3.1", "supports_streaming": True}]),
        ),
        "openrouter": ProviderAdapterConfig(
            name="openrouter",
            provider_type="openrouter",
            default_model="openai/gpt-4.1-mini",
            base_url="https://openrouter.ai/api/v1",
            capabilities=streaming_completion,
            models=_models("openrouter", [{"id": "openai/gpt-4.1-mini", "supports_streaming": True}]),
        ),
        "custom": ProviderAdapterConfig(
            name="custom",
            provider_type="custom",
            default_model="custom-model",
            capabilities=custom_completion,
            models=_models("custom", [{"id": "custom-model", "supports_streaming": True}]),
        ),
    }


def build_standard_provider_adapters(response_template: str = "{prompt}") -> Dict[str, StaticProviderAdapter]:
    return {
        name: StaticProviderAdapter(config, response_template=response_template)
        for name, config in build_standard_provider_configs().items()
    }
