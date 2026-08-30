from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from core.adaptive_context_real_provider_boundary import ALLOWED_MODELS
from core.production_runtime.manifest import (
    get_te_v7_artifact_path,
    TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT,
    TE_V7_STAGE108_FAKE_TRANSPORT_FREEZE,
)

PREFLIGHT_VERSION = "7.0.0-stage10.9"
MAX_PREFLIGHT_ATTEMPTS = 3
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")


@dataclass(frozen=True)
class PreflightAttemptPlan:
    attempt: int
    model: str
    timeout_seconds: int
    fallback_used: bool = False

    def valid(self) -> bool:
        return (
            self.attempt >= 1
            and self.model in ALLOWED_MODELS
            and self.timeout_seconds > 0
        )


@dataclass(frozen=True)
class RealProviderPreflightConfig:
    enabled: bool = False
    boundary_enabled: bool = False
    real_provider_enabled: bool = False
    authorization_id: str = ""
    provider: str = "nvidia"
    provider_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    model: str = "meta/llama-3.2-90b-vision-instruct"
    fallback_models: tuple[str, ...] = ()
    attempt_plan: tuple[PreflightAttemptPlan, ...] = ()
    max_retries: int = 1
    source_identity: str = ""
    source_fingerprint: str = ""
    chunk_count: int = 1
    single_chunk_only: bool = True
    single_controlled_session: bool = True
    resumed: bool = False
    artifact_path: str = field(default_factory=lambda: str(get_te_v7_artifact_path(".", "te_v7_stage109", TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT)))
    stage108_freeze_path: str = field(default_factory=lambda: str(get_te_v7_artifact_path(".", "te_v7_stage108", TE_V7_STAGE108_FAKE_TRANSPORT_FREEZE)))
    te_v6_manifest_path: str = "manifests/te_v600_final_release_manifest.json"

    def __post_init__(self) -> None:
        object.__setattr__(self, "fallback_models", tuple(self.fallback_models))
        object.__setattr__(self, "attempt_plan", tuple(self.attempt_plan))


def safe_identifier(value: str) -> bool:
    return bool(_SAFE_ID.fullmatch(value.strip()))


def sha256_shape(value: str) -> bool:
    normalized = value.strip().lower()
    return len(normalized) == 64 and all(char in "0123456789abcdef" for char in normalized)
