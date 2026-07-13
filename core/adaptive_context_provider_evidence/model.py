from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

PROVIDER_EVIDENCE_VERSION = "7.0.0-stage10.1"


@dataclass(frozen=True)
class ProviderRequestIdentity:
    pair_id: str
    run_kind: str
    set_name: str
    chunk_index: int
    source_hash: str
    chunk_hash: str
    model: str
    attempt: int
    resumed: bool = False
    minimum_output_tokens: int = 0


@dataclass(frozen=True)
class TokenUsageEvidence:
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    actual_input_tokens: int | None = None
    actual_output_tokens: int | None = None
    usage_source: str = "estimate"


@dataclass(frozen=True)
class ProviderTimingEvidence:
    pair_id: str
    run_kind: str
    set_name: str
    chunk_index: int
    source_hash: str
    chunk_hash: str
    model: str
    attempt: int
    status: str
    elapsed_ms: float | None
    started_at_utc: str
    finished_at_utc: str
    error_category: str = ""
    http_status: int | None = None
    external_provider_condition: bool = False
    fallback_used: bool = False
    token_usage: TokenUsageEvidence = TokenUsageEvidence()
    suspicious_short_output: bool = False
    real_provider_execution: bool = False
    content_redacted: bool = True
    version: str = PROVIDER_EVIDENCE_VERSION

    @property
    def timing_complete(self) -> bool:
        return self.elapsed_ms is not None and self.elapsed_ms >= 0 and bool(self.started_at_utc and self.finished_at_utc)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderEvidenceBundle:
    pair_id: str
    run_kind: str
    records: tuple[ProviderTimingEvidence, ...]
    excluded_resume_chunks: tuple[dict[str, object], ...] = ()
    status: str = "evidence_incomplete"
    evidence_complete: bool = False
    ready_for_benchmark: bool = False
    limitations: tuple[str, ...] = ()
    content_redacted: bool = True
    version: str = PROVIDER_EVIDENCE_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))
        object.__setattr__(self, "excluded_resume_chunks", tuple(self.excluded_resume_chunks))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request_evidence"] = payload.pop("records")
        return payload
