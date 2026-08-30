from __future__ import annotations

from dataclasses import dataclass

from core.adaptive_context_real_provider_boundary import (
    ALLOWED_CREDENTIAL_ENV,
    ALLOWED_MODELS,
    ALLOWED_PROVIDER_URLS,
)

HARNESS_VERSION = "7.0.0-stage10.5"
PROVIDER = "nvidia"
CREDENTIAL_ENV = "NVIDIA_API_KEY"


@dataclass(frozen=True)
class AuthorizedProviderHarnessConfig:
    boundary_enabled: bool = False
    real_provider_enabled: bool = False
    authorization_id: str = ""
    execution_mode: str = "fake"
    provider: str = PROVIDER
    provider_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    model: str = "meta/llama-3.2-90b-vision-instruct"
    session_id: str = ""
    single_chunk_only: bool = True
    single_controlled_session: bool = True

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.boundary_enabled:
            blockers.append("authorized-harness-boundary-enable-required")
        if not self.real_provider_enabled:
            blockers.append("authorized-harness-real-provider-enable-required")
        if not self.authorization_id.strip():
            blockers.append("authorized-harness-authorization-id-required")
        if self.execution_mode not in {"fake", "real"}:
            blockers.append("authorized-harness-execution-mode-invalid")
        if self.provider not in ALLOWED_CREDENTIAL_ENV:
            blockers.append("authorized-harness-provider-not-allowlisted")
        if self.provider_url not in ALLOWED_PROVIDER_URLS:
            blockers.append("authorized-harness-endpoint-not-allowlisted")
        if self.model not in ALLOWED_MODELS:
            blockers.append("authorized-harness-model-not-allowlisted")
        if ALLOWED_CREDENTIAL_ENV.get(self.provider) != CREDENTIAL_ENV:
            blockers.append("authorized-harness-credential-environment-invalid")
        if not self.session_id.strip():
            blockers.append("authorized-harness-session-id-required")
        if not self.single_chunk_only:
            blockers.append("authorized-harness-single-chunk-required")
        if not self.single_controlled_session:
            blockers.append("authorized-harness-single-session-required")
        return tuple(blockers)
