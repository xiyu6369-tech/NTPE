from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .config import PIPELINE_VERSION

EVIDENCE_STATUSES = frozenset({
    "evidence_complete_mock_only",
    "evidence_complete_provider_limited",
    "ready_for_benchmark",
    "evidence_incomplete",
    "excluded_resume",
    "rejected_provenance",
    "rejected_integrity",
})


@dataclass(frozen=True)
class ProviderEvidenceAttempt:
    attempt_number: int
    attempt_status: str
    elapsed_milliseconds: float | None
    retry_count: int
    fallback_used: bool
    timeout: bool
    http_503: bool
    external_condition_failure: bool
    estimated_input_tokens: int
    estimated_output_tokens: int
    suspicious_short_output: bool
    timing_complete: bool


@dataclass(frozen=True)
class ProviderEvidenceArtifact:
    session_id: str
    chunk_identity: str
    source_fingerprint: str
    chunk_fingerprint: str
    model: str
    attempts: tuple[ProviderEvidenceAttempt, ...]
    status: str
    evidence_provenance: str
    transport_provenance: str
    evidence_complete: bool
    ready_for_benchmark: bool
    payload_preserved: bool
    prompt_preserved: bool
    resume_excluded: bool
    short_output_suspicion: bool
    limitations: tuple[str, ...] = ()
    baseline_candidate_compared: bool = False
    production_readiness_evaluated: bool = False
    rollout_readiness_evaluated: bool = False
    translation_quality_evaluated: bool = False
    content_redacted: bool = True
    version: str = PIPELINE_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempts", tuple(self.attempts))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
