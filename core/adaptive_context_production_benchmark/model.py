from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

BENCHMARK_VERSION = "7.0.0-stage09"


@dataclass(frozen=True)
class BenchmarkContract:
    set_name: str
    source_file_hash: str
    chunk_count: int
    chunk_plan: tuple[str, ...]
    profile: str
    model: str
    api_timeout: int
    provider_attempts: int
    chunk_size: int
    max_output_tokens: int
    prompt_policy_version: str
    quality_v5_version: str
    retry_recovery_policy_version: str
    ace_enabled: bool
    rollout_percent: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "chunk_plan", tuple(self.chunk_plan))

    def comparison_values(self) -> dict[str, Any]:
        values = asdict(self)
        values.pop("ace_enabled", None)
        values.pop("rollout_percent", None)
        return values


@dataclass(frozen=True)
class ChunkEvidence:
    set_name: str
    chunk_index: int
    source_hash: str
    source_offset: str
    chunk_hash: str
    completion: str
    ace_state: str
    provider_calls: int = 0
    provider_attempts: int = 0
    provider_latency_ms: float | None = None
    timeout_count: int = 0
    http_503_count: int = 0
    execution_ms: float = 0.0
    prompt_tokens: int = 0
    context_tokens: int = 0
    qa_status: str = "unknown"
    quality_score: float | None = None
    omission_issues: int = 0
    unsupported_detail_issues: int = 0
    completeness_issues: int = 0
    naturalness_actions: int = 0
    naturalness_warnings: int = 0
    recovery_invocations: int = 0
    quality_evidence_complete: bool = False
    rollback_triggered: bool = False

    @property
    def pair_key(self) -> tuple[str, int, str, str, str]:
        return (self.set_name, self.chunk_index, self.source_hash, self.source_offset, self.chunk_hash)

    @property
    def provider_completed(self) -> bool:
        return self.completion == "provider_completed"


@dataclass(frozen=True)
class BenchmarkRun:
    run_kind: str
    mode: str
    stage: str
    contract: BenchmarkContract
    chunks: tuple[ChunkEvidence, ...] = ()
    execution_total_ms: float = 0.0
    rollback_triggered: bool = False
    artifact_integrity: bool = True
    provider_evidence_complete: bool = False
    status: str = "complete"
    limitations: tuple[str, ...] = ()
    content_redacted: bool = True
    version: str = BENCHMARK_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "chunks", tuple(self.chunks))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["chunk_evidence"] = payload.pop("chunks")
        return payload


@dataclass(frozen=True)
class BenchmarkComparison:
    status: str
    ready: bool
    contract_match: bool
    blockers: tuple[str, ...]
    limitations: tuple[str, ...]
    performance: dict[str, Any] = field(default_factory=dict)
    quality: dict[str, Any] = field(default_factory=dict)
    paired_chunks: tuple[dict[str, Any], ...] = ()
    content_redacted: bool = True
    version: str = BENCHMARK_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
