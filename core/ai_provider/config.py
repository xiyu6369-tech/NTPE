from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .adapters import ProviderAdapterConfig, StaticProviderAdapter, build_standard_provider_configs
from .contracts import ModelInfo, ProviderCapability
from .credentials import ProviderCredential, ProviderCredentialRegistry, mask_mapping
from .rate_limiter import RateLimiter
from .registry import ProviderRegistry
from .retry import RetryPolicy


DEFAULT_PROVIDER_ENV = {
    "nvidia": "NVIDIA_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "ollama": "OLLAMA_API_KEY",
    "custom": "NTPE_CUSTOM_PROVIDER_API_KEY",
}


@dataclass(frozen=True)
class ProviderProfile:
    name: str
    provider_type: str
    default_model: Optional[str] = None
    api_key: Optional[str] = None
    env_var: Optional[str] = None
    base_url: Optional[str] = None
    enabled: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    models: list[ModelInfo] = field(default_factory=list)
    capabilities: ProviderCapability = field(default_factory=ProviderCapability)
    retry: Dict[str, Any] = field(default_factory=dict)
    rate_limit: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_adapter_config(cls, config: ProviderAdapterConfig) -> "ProviderProfile":
        return cls(
            name=config.name,
            provider_type=config.provider_type,
            default_model=config.default_model,
            api_key=config.api_key,
            env_var=DEFAULT_PROVIDER_ENV.get(config.name),
            base_url=config.base_url,
            headers=dict(config.headers),
            models=list(config.models),
            capabilities=config.capabilities,
            metadata=dict(config.metadata),
        )

    @classmethod
    def from_dict(cls, name: str, payload: Mapping[str, Any], base: Optional["ProviderProfile"] = None) -> "ProviderProfile":
        source = base or cls.from_adapter_config(build_standard_provider_configs().get(name, ProviderAdapterConfig(name=name, provider_type=name)))
        models_payload = payload.get("models")
        models = source.models
        if isinstance(models_payload, list):
            models = [ModelInfo(provider=name, **item) for item in models_payload]
        capabilities_payload = payload.get("capabilities")
        capabilities = source.capabilities
        if isinstance(capabilities_payload, Mapping):
            base_cap = source.capabilities.to_dict()
            base_cap.update(dict(capabilities_payload))
            capabilities = ProviderCapability(**base_cap)
        return cls(
            name=name,
            provider_type=str(payload.get("provider_type", source.provider_type)),
            default_model=payload.get("default_model", source.default_model),
            api_key=payload.get("api_key", source.api_key),
            env_var=payload.get("env_var", source.env_var or DEFAULT_PROVIDER_ENV.get(name)),
            base_url=payload.get("base_url", source.base_url),
            enabled=bool(payload.get("enabled", source.enabled)),
            headers=dict(payload.get("headers", source.headers)),
            models=models,
            capabilities=capabilities,
            retry=dict(payload.get("retry", source.retry)),
            rate_limit=dict(payload.get("rate_limit", source.rate_limit)),
            metadata=dict(payload.get("metadata", source.metadata)),
        )

    def to_adapter_config(self, api_key: Optional[str] = None) -> ProviderAdapterConfig:
        return ProviderAdapterConfig(
            name=self.name,
            provider_type=self.provider_type,
            default_model=self.default_model,
            api_key=api_key if api_key is not None else self.api_key,
            base_url=self.base_url,
            headers=dict(self.headers),
            models=list(self.models),
            capabilities=self.capabilities,
            metadata=dict(self.metadata),
        )

    def credential(self) -> ProviderCredential:
        return ProviderCredential(provider=self.name, api_key=self.api_key, env_var=self.env_var, metadata=self.metadata)

    def masked(self) -> Dict[str, Any]:
        return mask_mapping(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "default_model": self.default_model,
            "api_key": self.api_key,
            "env_var": self.env_var,
            "base_url": self.base_url,
            "enabled": self.enabled,
            "headers": dict(self.headers),
            "models": [m.to_dict() for m in self.models],
            "capabilities": self.capabilities.to_dict(),
            "retry": dict(self.retry),
            "rate_limit": dict(self.rate_limit),
            "metadata": dict(self.metadata),
        }


@dataclass
class ProviderConfigLayer:
    default_provider: str = "nvidia"
    profiles: Dict[str, ProviderProfile] = field(default_factory=dict)
    credential_registry: ProviderCredentialRegistry = field(default_factory=ProviderCredentialRegistry)
    retry_defaults: Dict[str, Any] = field(default_factory=lambda: {"max_attempts": 3, "base_delay": 0.0, "max_delay": 0.0})
    rate_limit_defaults: Dict[str, Any] = field(default_factory=lambda: {"max_calls": 10**9, "window_seconds": 60})

    @classmethod
    def standard(cls, default_provider: str = "nvidia") -> "ProviderConfigLayer":
        profiles = {
            name: ProviderProfile.from_adapter_config(config)
            for name, config in build_standard_provider_configs().items()
        }
        layer = cls(default_provider=default_provider, profiles=profiles)
        for profile in profiles.values():
            layer.credential_registry.register(profile.credential())
        return layer

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProviderConfigLayer":
        layer = cls.standard(default_provider=str(payload.get("default_provider", "nvidia")))
        layer.retry_defaults.update(dict(payload.get("retry_defaults", {})))
        layer.rate_limit_defaults.update(dict(payload.get("rate_limit_defaults", {})))
        providers = payload.get("providers", {})
        if isinstance(providers, Mapping):
            for name, profile_payload in providers.items():
                if isinstance(profile_payload, Mapping):
                    layer.profiles[name] = ProviderProfile.from_dict(name, profile_payload, layer.profiles.get(name))
        layer.credential_registry = ProviderCredentialRegistry()
        for profile in layer.profiles.values():
            layer.credential_registry.register(profile.credential())
        return layer

    @classmethod
    def load(cls, path: str | Path) -> "ProviderConfigLayer":
        file_path = Path(path)
        if not file_path.exists():
            return cls.standard()
        with file_path.open("r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    def save_template(self, path: str | Path) -> Path:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as fh:
            json.dump(self.masked_manifest(), fh, ensure_ascii=False, indent=2)
        return file_path

    def enabled_profiles(self) -> Dict[str, ProviderProfile]:
        return {name: profile for name, profile in self.profiles.items() if profile.enabled}

    def build_registry(self, response_template: str = "{prompt}") -> ProviderRegistry:
        registry = ProviderRegistry()
        for name, profile in self.enabled_profiles().items():
            api_key = self.credential_registry.resolve_api_key(name)
            adapter = StaticProviderAdapter(profile.to_adapter_config(api_key=api_key), response_template=response_template)
            registry.register(adapter, default=(name == self.default_provider))
        if registry.list() and registry.default_name() not in registry.list():
            registry.set_default(registry.list()[0])
        return registry

    def build_retry_policy(self) -> RetryPolicy:
        return RetryPolicy(
            max_attempts=int(self.retry_defaults.get("max_attempts", 3)),
            base_delay_seconds=float(self.retry_defaults.get("base_delay_seconds", self.retry_defaults.get("base_delay", 0.0))),
            backoff_factor=float(self.retry_defaults.get("backoff_factor", 2.0)),
        )

    def build_rate_limiter(self) -> RateLimiter:
        return RateLimiter(
            max_calls=int(self.rate_limit_defaults.get("max_calls", 10**9)),
            window_seconds=int(self.rate_limit_defaults.get("window_seconds", 60)),
        )

    def validate_credentials(self) -> Dict[str, Dict[str, Any]]:
        local = {name for name, profile in self.profiles.items() if profile.provider_type in {"ollama", "custom"}}
        return self.credential_registry.validate_all(local_providers=local)

    def masked_manifest(self) -> Dict[str, Any]:
        return {
            "default_provider": self.default_provider,
            "providers": {name: profile.masked() for name, profile in self.profiles.items()},
            "credentials": self.credential_registry.masked(),
            "retry_defaults": dict(self.retry_defaults),
            "rate_limit_defaults": dict(self.rate_limit_defaults),
        }

    def manifest(self) -> Dict[str, Any]:
        payload = self.masked_manifest()
        payload["credential_validation"] = self.validate_credentials()
        return payload
