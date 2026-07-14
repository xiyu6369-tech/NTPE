from __future__ import annotations

from dataclasses import dataclass

from core.adaptive_context_authorized_provider_harness import (
    CREDENTIAL_ENV,
    AuthorizedProviderHarnessConfig,
)

CLI_VERSION = "7.0.0-stage10.6"


@dataclass(frozen=True)
class AuthorizedProviderCliConfig:
    boundary_enabled: bool = False
    real_provider_enabled: bool = False
    authorization_id: str = ""
    execution_mode: str = "fake"
    provider: str = "nvidia"
    provider_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    model: str = "meta/llama-3.3-70b-instruct"
    session_id: str = ""
    source_fingerprint: str = ""
    chunk_fingerprint: str = ""
    chunk_index: int = 1
    report_path: str = ""

    def harness_config(self) -> AuthorizedProviderHarnessConfig:
        return AuthorizedProviderHarnessConfig(
            boundary_enabled=self.boundary_enabled,
            real_provider_enabled=self.real_provider_enabled,
            authorization_id=self.authorization_id,
            execution_mode=self.execution_mode,
            provider=self.provider,
            provider_url=self.provider_url,
            model=self.model,
            session_id=self.session_id,
            single_chunk_only=True,
            single_controlled_session=True,
        )

    def validate(self) -> tuple[str, ...]:
        blockers = list(self.harness_config().validate())
        for label, value in (
            ("source", self.source_fingerprint),
            ("chunk", self.chunk_fingerprint),
        ):
            normalized = value.strip().lower()
            if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
                blockers.append(f"authorized-cli-{label}-fingerprint-invalid")
        if self.chunk_index != 1:
            blockers.append("authorized-cli-single-chunk-required")
        if CREDENTIAL_ENV != "NVIDIA_API_KEY":
            blockers.append("authorized-cli-credential-contract-invalid")
        return tuple(dict.fromkeys(blockers))
