from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from core.adaptive_context_provider_evidence_pipeline import ProviderEvidenceAttempt

from .config import CONTROLLED_RETRY_VERSION
from .token_evidence import ControlledRetryTokenEvidence

CONTROLLED_RETRY_STATUSES = frozenset({
    "controlled_retry_contract_prepared",
    "single_controlled_retry_completed",
    "single_controlled_retry_failed",
    "blocked",
})


@dataclass(frozen=True)
class ControlledRetryArtifact:
    stage: str
    status: str
    prior_invocation_integrity: str
    prior_invocation_status: str
    prior_timeout_evidence_valid: bool
    prior_timeout_confirmed: bool
    prior_network_requests: int
    invocation_id: str
    chunk_identity: str
    source_fingerprint: str
    model: str
    timeout_seconds: int
    attempt_limit: int
    fallback_allowed: bool
    attempt_count: int
    attempts: tuple[ProviderEvidenceAttempt, ...]
    token_evidence: ControlledRetryTokenEvidence
    timeout_detected: bool
    http_503_detected: bool
    real_provider_execution: bool
    network_requests: int
    retry_executed: bool
    translation_output_generated: bool
    payload_preserved: bool
    prompt_preserved: bool
    review_status: str
    human_review_required: bool = True
    comparison_executed: bool = False
    readiness_evaluated: bool = False
    baseline_created: bool = False
    candidate_created: bool = False
    production_ready: bool = False
    content_redacted: bool = True
    version: str = CONTROLLED_RETRY_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempts", tuple(self.attempts))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControlledRetryResult:
    artifact: ControlledRetryArtifact
    blockers: tuple[str, ...] = ()
    review_text: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "blockers", tuple(self.blockers))
