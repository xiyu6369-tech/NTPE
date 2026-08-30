from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.adaptive_context_real_provider_boundary import ALLOWED_MODELS, ALLOWED_PROVIDER_URLS
from core.adaptive_context_real_provider_preflight import safe_identifier
from core.production_runtime.manifest import (
    get_te_v7_artifact_path,
    TE_V7_STAGE1010_SINGLE_REAL_INVOCATION,
    TE_V7_STAGE10101_CONTROLLED_RETRY,
    TE_V7_STAGE10101_TRANSLATION_REVIEW,
)

CONTROLLED_RETRY_VERSION = "7.0.0-stage10.10.1"
CONTROLLED_RETRY_AUTHORIZATION_TOKEN = (
    "AUTHORIZE_NTPE_TE_V7_STAGE10101_SINGLE_CONTROLLED_RETRY"
)
DEFAULT_PRIOR_ARTIFACT_PATH = "artifacts/te_v7_stage1010/TE_V7_STAGE1010_SINGLE_REAL_INVOCATION.json"
DEFAULT_ARTIFACT_PATH = "artifacts/te_v7_stage10101/TE_V7_STAGE10101_CONTROLLED_RETRY.json"
DEFAULT_REVIEW_PATH = "artifacts/te_v7_stage10101/review/TE_V7_STAGE10101_TRANSLATION_REVIEW.txt"
DEFAULT_SOURCE_PATH = "tests/literary/Golden_Set/original_ko.txt"
FROZEN_TIMEOUT_SECONDS = 180
FROZEN_OUTPUT_TOKEN_BUDGET = 800


@dataclass(frozen=True)
class ControlledProviderRetryConfig:
    enabled: bool = False
    boundary_enabled: bool = False
    real_provider_enabled: bool = False
    authorization_id: str = ""
    execution_authorization_token: str = field(default="", repr=False, compare=False)
    execution_mode: str = "fake"
    provider: str = "nvidia"
    provider_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    model: str = "meta/llama-3.2-90b-vision-instruct"
    invocation_id: str = "stage10101-controlled-retry-001"
    source_path: str = DEFAULT_SOURCE_PATH
    chunk_index: int = 1
    chunk_size: int = 600
    chunk_count: int = 1
    single_chunk_only: bool = True
    single_controlled_session: bool = True
    resumed: bool = False
    timeout_seconds: int = FROZEN_TIMEOUT_SECONDS
    attempt_limit: int = 1
    fallback_allowed: bool = False
    prior_artifact_path: str = DEFAULT_PRIOR_ARTIFACT_PATH
    artifact_path: str = DEFAULT_ARTIFACT_PATH
    review_path: str = DEFAULT_REVIEW_PATH

    def validate_static(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.enabled:
            blockers.append("controlled-retry-disabled")
        if not self.boundary_enabled:
            blockers.append("controlled-retry-boundary-enable-required")
        if not self.real_provider_enabled:
            blockers.append("controlled-retry-real-provider-enable-required")
        if not self.authorization_id.strip():
            blockers.append("controlled-retry-authorization-id-required")
        elif not safe_identifier(self.authorization_id):
            blockers.append("controlled-retry-authorization-id-invalid")
        if not self.execution_authorization_token:
            blockers.append("controlled-retry-execution-authorization-required")
        elif self.execution_authorization_token != CONTROLLED_RETRY_AUTHORIZATION_TOKEN:
            blockers.append("controlled-retry-execution-authorization-invalid")
        if self.execution_mode not in {"fake", "real"}:
            blockers.append("controlled-retry-execution-mode-invalid")
        if self.provider != "nvidia" or self.provider_url not in ALLOWED_PROVIDER_URLS:
            blockers.append("controlled-retry-endpoint-not-allowlisted")
        if self.model not in ALLOWED_MODELS:
            blockers.append("controlled-retry-model-not-allowlisted")
        if not safe_identifier(self.invocation_id):
            blockers.append("controlled-retry-invocation-id-invalid")
        if not self.single_chunk_only or self.chunk_count != 1 or self.chunk_index != 1:
            blockers.append("controlled-retry-single-chunk-required")
        if not self.single_controlled_session:
            blockers.append("controlled-retry-single-session-required")
        if self.resumed:
            blockers.append("controlled-retry-resume-forbidden")
        if self.chunk_size != 600:
            blockers.append("controlled-retry-chunk-size-frozen")
        if self.timeout_seconds != FROZEN_TIMEOUT_SECONDS:
            blockers.append("controlled-retry-timeout-frozen")
        if self.attempt_limit != 1:
            blockers.append("controlled-retry-attempt-limit-frozen")
        if self.fallback_allowed:
            blockers.append("controlled-retry-fallback-forbidden")
        return tuple(dict.fromkeys(blockers))
