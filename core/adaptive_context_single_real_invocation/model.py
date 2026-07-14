from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from core.adaptive_context_provider_evidence_pipeline import ProviderEvidenceAttempt

from .config import INVOCATION_VERSION

INVOCATION_STATUSES = frozenset({
    "stage1010a_fake_transport_validated",
    "single_real_invocation_completed",
    "single_real_invocation_failed",
    "blocked",
})


@dataclass(frozen=True)
class OutputGuardResult:
    accepted_for_human_review: bool
    empty_output: bool
    suspicious_short_output: bool
    hangul_residue_signal: bool
    obvious_truncation: bool
    response_format_invalid: bool
    provider_refusal: bool


@dataclass(frozen=True)
class SingleRealInvocationArtifact:
    stage: str
    status: str
    review_status: str
    chunk_identity: str
    source_fingerprint: str
    model: str
    attempt_count: int
    attempts: tuple[ProviderEvidenceAttempt, ...]
    total_retry_latency_ms: float
    timeout_detected: bool
    http_503_detected: bool
    fallback_used: bool
    estimated_input_tokens: int
    estimated_output_tokens: int
    real_provider_execution: bool
    network_requests: int
    translation_output_generated: bool
    payload_preserved: bool
    prompt_preserved: bool
    empty_output: bool
    suspicious_short_output: bool
    hangul_residue_signal: bool
    obvious_truncation: bool
    response_format_invalid: bool
    provider_refusal: bool
    human_review_required: bool = True
    comparison_executed: bool = False
    readiness_evaluated: bool = False
    baseline_created: bool = False
    candidate_created: bool = False
    production_ready: bool = False
    content_redacted: bool = True
    version: str = INVOCATION_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempts", tuple(self.attempts))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SingleRealInvocationRunResult:
    artifact: SingleRealInvocationArtifact
    blockers: tuple[str, ...] = ()
    review_text: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "blockers", tuple(self.blockers))
