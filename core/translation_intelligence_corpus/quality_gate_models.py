"""Immutable data models for the TIC Batch 7 offline quality gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


GATE_STATUSES = frozenset(
    {"pass", "fail", "not_applicable", "insufficient_evidence", "invalid_input"}
)


def _frozen_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True, slots=True)
class TranslationCandidate:
    candidate_id: str | None
    source_text: str
    translation_text: str
    source_reference: str | None = None
    translation_reference: str | None = None
    case_id: str | None = None
    failure_case_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _frozen_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class QualityGateResult:
    candidate_id: str
    source_sha256: str
    translation_sha256: str
    applicable_regressions: tuple[str, ...]
    passed_regressions: tuple[str, ...]
    failed_regressions: tuple[str, ...]
    skipped_regressions: tuple[str, ...]
    gate_status: str
    gate_blocking: bool
    quality_candidate_allowed: bool
    review_ready: bool
    regression_safe: bool
    failure_reasons: tuple[str, ...]
    evaluation_details: tuple[Mapping[str, Any], ...]
    provider_executed: bool = False
    network_requests: int = 0
    disk_writes: int = 0
    integrity: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.gate_status not in GATE_STATUSES:
            raise ValueError(f"invalid gate status: {self.gate_status}")
        object.__setattr__(
            self,
            "evaluation_details",
            tuple(_frozen_mapping(item) for item in self.evaluation_details),
        )
        object.__setattr__(self, "integrity", _frozen_mapping(self.integrity))

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "source_sha256": self.source_sha256,
            "translation_sha256": self.translation_sha256,
            "applicable_regressions": list(self.applicable_regressions),
            "passed_regressions": list(self.passed_regressions),
            "failed_regressions": list(self.failed_regressions),
            "skipped_regressions": list(self.skipped_regressions),
            "gate_status": self.gate_status,
            "gate_blocking": self.gate_blocking,
            "quality_candidate_allowed": self.quality_candidate_allowed,
            "review_ready": self.review_ready,
            "regression_safe": self.regression_safe,
            "failure_reasons": list(self.failure_reasons),
            "evaluation_details": [dict(item) for item in self.evaluation_details],
            "provider_executed": self.provider_executed,
            "network_requests": self.network_requests,
            "disk_writes": self.disk_writes,
            "integrity": dict(self.integrity),
        }


@dataclass(frozen=True, slots=True)
class QualityGateSuiteResult:
    results: tuple[QualityGateResult, ...]
    total_candidates: int
    pass_count: int
    fail_count: int
    not_applicable_count: int
    insufficient_evidence_count: int
    invalid_input_count: int
    all_regression_safe: bool
    provider_executed: bool = False
    network_requests: int = 0
    disk_writes: int = 0
    integrity: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "integrity", _frozen_mapping(self.integrity))

    def as_dict(self) -> dict[str, Any]:
        return {
            "results": [item.as_dict() for item in self.results],
            "total_candidates": self.total_candidates,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "not_applicable_count": self.not_applicable_count,
            "insufficient_evidence_count": self.insufficient_evidence_count,
            "invalid_input_count": self.invalid_input_count,
            "all_regression_safe": self.all_regression_safe,
            "provider_executed": self.provider_executed,
            "network_requests": self.network_requests,
            "disk_writes": self.disk_writes,
            "integrity": dict(self.integrity),
        }
