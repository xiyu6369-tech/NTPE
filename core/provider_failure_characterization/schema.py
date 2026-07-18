from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from .failure_types import FailureType


SCHEMA_VERSION = "1.0"
POLICY_VERSION = "lcr-batch108-pfc-v1"


@dataclass(frozen=True)
class FailureClassification:
    failure_type: FailureType
    classification: str
    reason_code: str
    matched_field: str
    deterministic: bool = True
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["failure_type"] = self.failure_type.value
        return value


@dataclass(frozen=True)
class FailureExecutionPolicy:
    failure_type: FailureType
    retry_allowed: bool
    fallback_allowed: bool
    manual_review_required: bool
    evidence_only: bool
    execution_consumed: bool
    rollback_required: bool
    production_safe: bool
    provider_investigation_required: bool
    policy_version: str = POLICY_VERSION

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["failure_type"] = self.failure_type.value
        return value


@dataclass(frozen=True)
class DecisionInput:
    failure_type: FailureType
    authorization_consumed: bool
    execution_claim_consumed: bool
    provider_request_count: int
    candidate_available: bool = False
    semantic_verification_run: bool = False
    production_modified: bool = False


@dataclass(frozen=True)
class ExecutionDecision:
    status: str
    actions: tuple[str, ...]
    retry_allowed: bool
    fallback_allowed: bool
    authorization_consumed: bool
    execution_consumed: bool
    rollback_required: bool
    manual_review_required: bool
    provider_investigation_required: bool
    production_safe: bool
    policy_version: str = POLICY_VERSION

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionSummary:
    execution_id: str
    provider: str
    model: str
    failure_type: FailureType
    classification: str
    decision: str
    authorization_consumed: bool
    execution_consumed: bool
    candidate_available: bool
    semantic_verification_run: bool
    rollback_required: bool
    manual_review_required: bool
    production_safe: bool
    retry_allowed: bool
    fallback_allowed: bool
    provider_request_count: int
    network_request_count: int
    evidence_fingerprint: str
    source_execution_immutable: bool = True
    batch108_provider_requests_added: int = 0
    batch108_network_requests_added: int = 0
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["failure_type"] = self.failure_type.value
        return value


ExecutionRecord = Mapping[str, object]

