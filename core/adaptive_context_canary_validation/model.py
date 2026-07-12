from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

@dataclass(frozen=True)
class CanaryProductionValidationReport:
    version: str
    stage: str
    status: str
    ready: bool
    provider_status: str
    records: int
    attempted_records: int
    activated_records: int
    fallback_records: int
    target_chunk: int
    baseline_context_tokens: int
    canary_context_tokens: int
    estimated_tokens_saved: int
    payload_changed_records: int
    provider_calls_added: int
    fallback_reasons: tuple[str, ...]
    target_chunk_completed: bool
    canary_latency_total_ms: float
    canary_latency_average_ms: float
    blockers: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "blockers", tuple(self.blockers))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        object.__setattr__(self, "fallback_reasons", tuple(self.fallback_reasons))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "stage": self.stage,
            "status": self.status,
            "ready": self.ready,
            "provider_status": self.provider_status,
            "records": self.records,
            "attempted_records": self.attempted_records,
            "activated_records": self.activated_records,
            "fallback_records": self.fallback_records,
            "target_chunk": self.target_chunk,
            "baseline_context_tokens": self.baseline_context_tokens,
            "canary_context_tokens": self.canary_context_tokens,
            "estimated_tokens_saved": self.estimated_tokens_saved,
            "payload_changed_records": self.payload_changed_records,
            "provider_calls_added": self.provider_calls_added,
            "fallback_reasons": list(self.fallback_reasons),
            "target_chunk_completed": self.target_chunk_completed,
            "canary_latency_total_ms": self.canary_latency_total_ms,
            "canary_latency_average_ms": self.canary_latency_average_ms,
            "blockers": list(self.blockers),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
        }
