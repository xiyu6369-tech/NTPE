from __future__ import annotations

import os
from collections.abc import Mapping

from .models import ProviderDefinition


def provider_catalog(environment: Mapping[str, str] | None = None) -> tuple[ProviderDefinition, ...]:
    values = os.environ if environment is None else environment
    return (
        ProviderDefinition(
            provider_id="nvidia",
            display_name="NVIDIA API",
            available=True,
            configured=bool(values.get("NVIDIA_API_KEY")),
            requires_api_key=True,
            environment_variable="NVIDIA_API_KEY",
            supports_model_listing=False,
            network_required=True,
            status_reason="existing_cli_integration",
        ),
        ProviderDefinition(
            provider_id="gemini",
            display_name="Google Gemini",
            available=False,
            configured=bool(values.get("GEMINI_API_KEY")),
            requires_api_key=True,
            environment_variable="GEMINI_API_KEY",
            supports_model_listing=False,
            network_required=True,
            status_reason="not_yet_integrated",
        ),
    )


def get_provider(provider_id: str, environment: Mapping[str, str] | None = None) -> ProviderDefinition | None:
    return next((provider for provider in provider_catalog(environment) if provider.provider_id == provider_id), None)
