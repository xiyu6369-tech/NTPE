from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from core.ai_provider import (
    AIProvider,
    FallbackStrategy,
    ProviderCapability,
    ProviderConfigLayer,
    ProviderError,
    ProviderManager,
    ProviderRequest,
    ProviderResponse,
    ProviderRouter,
    ProviderRuntimeExecutionPolicy,
    ProviderRegistry,
    RateLimiter,
    RetryPolicy,
)

from .nvidia_client import NvidiaClient


RETRYABLE_PROVIDER_ERROR_PATTERNS = (
    "503",
    "429",
    "resourceexhausted",
    "degraded",
    "cannot be invoked",
    "rate limit",
    "too many requests",
    "service unavailable",
    "timeout",
    "timed out",
    "temporarily unavailable",
)

NON_RETRYABLE_PROVIDER_ERROR_PATTERNS = (
    "401",
    "403",
    "408",
    "unauthorized",
    "invalid api key",
    "permission denied",
)


def is_retryable_translation_provider_error(error: str, patterns: Iterable[str] = RETRYABLE_PROVIDER_ERROR_PATTERNS) -> bool:
    lowered = str(error or "").lower()
    if any(pattern in lowered for pattern in NON_RETRYABLE_PROVIDER_ERROR_PATTERNS):
        return False
    return any(str(pattern).lower() in lowered for pattern in patterns)


@dataclass(frozen=True)
class TranslationProviderSettings:
    fallback_models: tuple[str, ...] = ()
    retry_attempts: int = 1
    retry_base_delay_seconds: float = 0.0
    retry_backoff_factor: float = 2.0
    retryable_error_patterns: tuple[str, ...] = RETRYABLE_PROVIDER_ERROR_PATTERNS

    @classmethod
    def load(cls, root: Path) -> "TranslationProviderSettings":
        config_path = root / "config" / "provider_config.json"
        payload: dict[str, Any] = {}
        if config_path.exists():
            try:
                import json

                payload = json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                payload = {}

        engine_payload = payload.get("translation_engine_v3", {})
        if not isinstance(engine_payload, dict):
            engine_payload = {}
        retry_payload = engine_payload.get("retry_defaults", {})
        if not isinstance(retry_payload, dict):
            retry_payload = {}

        configured_models: list[str] = []
        models_payload = engine_payload.get("fallback_models", [])
        if isinstance(models_payload, list):
            configured_models.extend(str(item).strip() for item in models_payload)
        env_models = os.environ.get(str(engine_payload.get("fallback_models_env", "NTPE_FALLBACK_MODELS")), "")
        configured_models.extend(str(item).strip() for item in env_models.split(","))
        patterns_payload = engine_payload.get("retryable_error_patterns", RETRYABLE_PROVIDER_ERROR_PATTERNS)
        if not isinstance(patterns_payload, list):
            patterns_payload = list(RETRYABLE_PROVIDER_ERROR_PATTERNS)

        deduped: list[str] = []
        for model in configured_models:
            if model and model not in deduped:
                deduped.append(model)

        return cls(
            fallback_models=tuple(deduped),
            retry_attempts=max(1, int(retry_payload.get("max_attempts", 1))),
            retry_base_delay_seconds=max(0.0, float(retry_payload.get("base_delay_seconds", 0.0))),
            retry_backoff_factor=max(1.0, float(retry_payload.get("backoff_factor", 2.0))),
            retryable_error_patterns=tuple(str(item) for item in patterns_payload if str(item).strip()),
        )


class NvidiaTranslationProvider(AIProvider):
    name = "nvidia"
    provider_type = "nvidia"
    capabilities = ProviderCapability(
        completion=True,
        streaming=False,
        model_discovery=True,
        token_usage=False,
        cost_statistics=False,
        health_check=True,
        rate_limit=True,
        retry=True,
    )

    def __init__(
        self,
        *,
        name: str,
        api_key: str | None,
        api_url: str,
        timeout: int,
        rpm_limit: int,
        default_model: str,
        force_default_model: bool = False,
        retryable_error_patterns: Iterable[str] = RETRYABLE_PROVIDER_ERROR_PATTERNS,
    ) -> None:
        self.name = name
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout
        self.rpm_limit = rpm_limit
        self.default_model = default_model
        self.force_default_model = force_default_model
        self.retryable_error_patterns = tuple(retryable_error_patterns)

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        metadata = request.metadata or {}
        try:
            client = NvidiaClient(
                api_key=self.api_key,
                api_url=self.api_url,
                timeout=self.timeout,
                rpm_limit=self.rpm_limit,
            )
            model = self.default_model if self.force_default_model else request.model or self.default_model
            text = client.chat(
                model=model,
                system_prompt=str(metadata.get("system_prompt", "")),
                user_prompt=request.prompt,
                temperature=request.temperature if request.temperature is not None else float(metadata.get("temperature", 0.15)),
                top_p=float(metadata.get("top_p", 0.85)),
                max_tokens=request.max_tokens or int(metadata.get("max_tokens", 4000)),
            )
            return ProviderResponse(
                text=text,
                provider=self.name,
                model=model,
                metadata={"transport": "nvidia_client", "provider_type": self.provider_type},
            )
        except Exception as exc:
            message = str(exc)
            raise ProviderError(
                message=message,
                provider=self.name,
                retryable=is_retryable_translation_provider_error(message, self.retryable_error_patterns),
            ) from exc

    def health(self) -> dict[str, Any]:
        payload = super().health()
        payload.update({"configured": bool(self.api_key or os.environ.get("NVIDIA_API_KEY")), "base_url": self.api_url})
        return payload


def build_translation_provider_manager(
    *,
    root: Path,
    api_key: str | None,
    primary_model: str,
    api_url: str,
    timeout: int,
    rpm_limit: int,
    max_attempts: int | None = None,
    retry_base_delay_seconds: float | None = None,
) -> ProviderManager:
    config_layer = ProviderConfigLayer.load(root / "config" / "provider_config.json")
    settings = TranslationProviderSettings.load(root)
    registry = ProviderRegistry()

    primary = NvidiaTranslationProvider(
        name="nvidia",
        api_key=api_key,
        api_url=api_url,
        timeout=timeout,
        rpm_limit=rpm_limit,
        default_model=primary_model,
        retryable_error_patterns=settings.retryable_error_patterns,
    )
    registry.register(primary, default=True)

    fallback_names: list[str] = []
    for model in _dedupe_models(settings.fallback_models, exclude={primary_model}):
        name = f"nvidia_fallback_{_safe_provider_suffix(model)}"
        registry.register(
            NvidiaTranslationProvider(
                name=name,
                api_key=api_key,
                api_url=api_url,
                timeout=timeout,
                rpm_limit=rpm_limit,
                default_model=model,
                force_default_model=True,
                retryable_error_patterns=settings.retryable_error_patterns,
            )
        )
        fallback_names.append(name)

    max_attempts = max_attempts if max_attempts is not None else settings.retry_attempts
    retry_base_delay_seconds = retry_base_delay_seconds if retry_base_delay_seconds is not None else settings.retry_base_delay_seconds
    retry_policy = RetryPolicy(
        max_attempts=max_attempts,
        base_delay_seconds=retry_base_delay_seconds,
        backoff_factor=settings.retry_backoff_factor,
    )
    return ProviderManager(
        registry=registry,
        router=ProviderRouter(default_provider="nvidia"),
        retry_policy=retry_policy,
        rate_limiter=RateLimiter(max_calls=10**9),
        fallback=FallbackStrategy(fallback_names),
        config_layer=config_layer,
        execution_policy=ProviderRuntimeExecutionPolicy(retry_policy=retry_policy, rate_limiter=RateLimiter(max_calls=10**9)),
    )


def _dedupe_models(models: Iterable[str], *, exclude: set[str]) -> list[str]:
    result: list[str] = []
    for model in models:
        model = str(model or "").strip()
        if model and model not in exclude and model not in result:
            result.append(model)
    return result


def _safe_provider_suffix(model: str) -> str:
    suffix = re.sub(r"[^a-zA-Z0-9]+", "_", model).strip("_").lower()
    return suffix[:80] or "model"
