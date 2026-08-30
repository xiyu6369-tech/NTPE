from __future__ import annotations

from dataclasses import dataclass, field

from core.adaptive_context_real_provider_boundary import ALLOWED_MODELS, ALLOWED_PROVIDER_URLS
from core.adaptive_context_real_provider_preflight import PreflightAttemptPlan, safe_identifier
from core.production_runtime.manifest import get_te_v7_artifact_path, TE_V7_STAGE1010_SINGLE_REAL_INVOCATION, TE_V7_STAGE1010_TRANSLATION_REVIEW, TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT

INVOCATION_VERSION = "7.0.0-stage10.10A"
EXECUTION_AUTHORIZATION_TOKEN = "AUTHORIZE_NTPE_TE_V7_STAGE1010_SINGLE_REAL_INVOCATION"
DEFAULT_SOURCE_PATH = "tests/literary/Golden_Set/original_ko.txt"
DEFAULT_ARTIFACT_PATH = field(default_factory=lambda: str(get_te_v7_artifact_path(".", "te_v7_stage1010", TE_V7_STAGE1010_SINGLE_REAL_INVOCATION)))
DEFAULT_REVIEW_PATH = field(default_factory=lambda: str(get_te_v7_artifact_path(".", "te_v7_stage1010", TE_V7_STAGE1010_TRANSLATION_REVIEW)))
DEFAULT_STAGE109_PATH = field(default_factory=lambda: str(get_te_v7_artifact_path(".", "te_v7_stage109", TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT)))


@dataclass(frozen=True)
class SingleRealInvocationConfig:
    enabled: bool = False
    boundary_enabled: bool = False
    real_provider_enabled: bool = False
    authorization_id: str = ""
    execution_authorization_token: str = field(default="", repr=False, compare=False)
    execution_mode: str = "fake"
    provider: str = "nvidia"
    provider_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    model: str = "meta/llama-3.2-90b-vision-instruct"
    session_id: str = "stage1010-single-session"
    source_path: str = "tests/literary/Golden_Set/original_ko.txt"
    chunk_index: int = 1
    chunk_size: int = 600
    chunk_count: int = 1
    single_chunk_only: bool = True
    single_controlled_session: bool = True
    resumed: bool = False
    attempt_plan: tuple[PreflightAttemptPlan, ...] = ()
    max_retries: int = 1
    artifact_path: str = DEFAULT_ARTIFACT_PATH
    review_path: str = DEFAULT_REVIEW_PATH
    stage109_artifact_path: str = DEFAULT_STAGE109_PATH

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_plan", tuple(self.attempt_plan))

    def validate_static(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.enabled:
            blockers.append("single-real-invocation-disabled")
        if not self.boundary_enabled:
            blockers.append("single-real-invocation-boundary-enable-required")
        if not self.real_provider_enabled:
            blockers.append("single-real-invocation-real-provider-enable-required")
        if not self.authorization_id.strip():
            blockers.append("single-real-invocation-authorization-id-required")
        elif not safe_identifier(self.authorization_id):
            blockers.append("single-real-invocation-authorization-id-invalid")
        if not self.execution_authorization_token:
            blockers.append("single-real-invocation-execution-authorization-required")
        elif self.execution_authorization_token != EXECUTION_AUTHORIZATION_TOKEN:
            blockers.append("single-real-invocation-execution-authorization-invalid")
        if self.execution_mode not in {"fake", "real"}:
            blockers.append("single-real-invocation-execution-mode-invalid")
        if self.provider != "nvidia" or self.provider_url not in ALLOWED_PROVIDER_URLS:
            blockers.append("single-real-invocation-endpoint-not-allowlisted")
        if self.model not in ALLOWED_MODELS:
            blockers.append("single-real-invocation-model-not-allowlisted")
        if not safe_identifier(self.session_id):
            blockers.append("single-real-invocation-session-id-invalid")
        if not self.single_chunk_only or self.chunk_count != 1 or self.chunk_index != 1:
            blockers.append("single-real-invocation-single-chunk-required")
        if not self.single_controlled_session:
            blockers.append("single-real-invocation-single-session-required")
        if self.resumed:
            blockers.append("single-real-invocation-resume-forbidden")
        if self.chunk_size != 600:
            blockers.append("single-real-invocation-chunk-size-frozen")
        if not self.attempt_plan:
            blockers.append("single-real-invocation-attempt-plan-required")
        elif (
            len(self.attempt_plan) > 3
            or len(self.attempt_plan) - 1 > self.max_retries
            or [plan.attempt for plan in self.attempt_plan] != list(range(1, len(self.attempt_plan) + 1))
            or any(not plan.valid() for plan in self.attempt_plan)
            or any((plan.attempt == 1) == plan.fallback_used for plan in self.attempt_plan)
        ):
            blockers.append("single-real-invocation-attempt-plan-invalid")
        return tuple(dict.fromkeys(blockers))
