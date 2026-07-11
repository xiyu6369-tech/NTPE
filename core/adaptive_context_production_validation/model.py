from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class ProductionShadowValidationReport:
    version: str
    stage: str
    status: str
    execution_mode: str
    provider_execution_requested: bool
    provider_execution_observed: bool
    shadow_records: int
    payload_equivalent_records: int
    payload_mismatch_records: int
    provider_calls_added: int
    admissible_records: int
    fallback_records: int
    baseline_context_tokens: int
    ace_context_tokens: int
    estimated_tokens_saved: int
    ace_latency_total_ms: float
    ace_latency_average_ms: float
    regression_status: str
    blockers: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def ready(self) -> bool:
        return self.status == "pass" and not self.blockers

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "stage": self.stage,
            "status": self.status,
            "ready": self.ready,
            "execution_mode": self.execution_mode,
            "provider_execution_requested": self.provider_execution_requested,
            "provider_execution_observed": self.provider_execution_observed,
            "shadow_records": self.shadow_records,
            "payload_equivalent_records": self.payload_equivalent_records,
            "payload_mismatch_records": self.payload_mismatch_records,
            "provider_calls_added": self.provider_calls_added,
            "admissible_records": self.admissible_records,
            "fallback_records": self.fallback_records,
            "baseline_context_tokens": self.baseline_context_tokens,
            "ace_context_tokens": self.ace_context_tokens,
            "estimated_tokens_saved": self.estimated_tokens_saved,
            "ace_latency_total_ms": self.ace_latency_total_ms,
            "ace_latency_average_ms": self.ace_latency_average_ms,
            "regression_status": self.regression_status,
            "blockers": list(self.blockers),
            "metadata": dict(self.metadata),
        }
