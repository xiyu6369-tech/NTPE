from __future__ import annotations

from dataclasses import dataclass

BOUNDARY_VERSION = "7.0.0-stage10.4"
ALLOWED_PROVIDER_URLS = frozenset({
    "https://integrate.api.nvidia.com/v1/chat/completions",
})
ALLOWED_MODELS = frozenset({"meta/llama-3.3-70b-instruct"})
ALLOWED_CREDENTIAL_ENV = {"nvidia": "NVIDIA_API_KEY"}


@dataclass(frozen=True)
class RealProviderBoundaryConfig:
    enabled: bool = False
    enable_real_provider: bool = False
    execution_mode: str = "fake"
    authorization_id: str = ""
    provider: str = "nvidia"
    provider_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    model: str = "meta/llama-3.3-70b-instruct"
    credential_env: str = "NVIDIA_API_KEY"
    pair_id: str = ""
    run_kind: str = "baseline"
    single_chunk_only: bool = True

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.enabled:
            blockers.append("real-provider-boundary-explicit-enable-required")
        if self.execution_mode not in {"fake", "real"}:
            blockers.append("real-provider-boundary-execution-mode-invalid")
        if self.execution_mode == "real":
            if not self.enable_real_provider:
                blockers.append("real-provider-additional-explicit-enable-required")
            if not self.authorization_id:
                blockers.append("real-provider-separate-authorization-required")
        elif self.enable_real_provider:
            blockers.append("fake-bridge-cannot-claim-real-provider-enable")
        if self.provider not in ALLOWED_CREDENTIAL_ENV:
            blockers.append("provider-not-allowlisted")
        if self.provider_url not in ALLOWED_PROVIDER_URLS:
            blockers.append("provider-url-not-allowlisted")
        if self.model not in ALLOWED_MODELS:
            blockers.append("provider-model-not-allowlisted")
        if ALLOWED_CREDENTIAL_ENV.get(self.provider) != self.credential_env:
            blockers.append("provider-credential-environment-not-allowlisted")
        if not self.pair_id:
            blockers.append("real-provider-boundary-pair-id-required")
        if self.run_kind not in {"baseline", "candidate"}:
            blockers.append("real-provider-boundary-run-kind-invalid")
        if not self.single_chunk_only:
            blockers.append("real-provider-boundary-single-chunk-required")
        return tuple(blockers)
