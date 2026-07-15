from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PipelineStageStatus:
    stage: str
    status: str
    artifact_reference: str
    artifact_sha256: str
    validation_status: str
    applied: bool = False


@dataclass(frozen=True)
class IntegrationBoundary:
    network_requests: int = 0
    real_provider_executed: bool = False
    provider_executed: bool = False
    runtime_executed: bool = False
    new_translation_generated: bool = False
    translation_generated: bool = False
    translation_quality_improved: bool = False
    prompt_modified: bool = False
    prompt_builder_modified: bool = False
    runtime_modified: bool = False
    provider_modified: bool = False
    translation_strategy_modified: bool = False
    plans_applied: int = 0
    decisions_applied: int = 0
    decision_applied: bool = False
    approved_cases_created: int = 0
    approved_translations_added: int = 0
    existing_approved_translations_modified: int = 0
    golden_corpus_content_modified: bool = False
    baseline_created: bool = False
    candidate_created: bool = False
    comparison_executed: bool = False
    readiness_evaluated: bool = False
    stage118_started: bool = False


@dataclass(frozen=True)
class IntegrityVerificationResult:
    valid: bool
    failed_stage: str | None = None
    failed_reference: str | None = None
    expected_sha256: str | None = None
    actual_sha256: str | None = None


@dataclass(frozen=True)
class QualityFrameworkIntegration:
    integration_id: str
    schema_version: str
    created_at: str
    source_case_id: str
    defects_reference: str
    defects_sha256: str
    metrics_reference: str
    metrics_sha256: str
    review_artifact_reference: str
    review_artifact_sha256: str
    improvement_plan_reference: str
    improvement_plan_sha256: str
    human_decision_reference: str
    human_decision_sha256: str
    corpus_governance_reference: str
    corpus_governance_sha256: str
    golden_corpus_reference: str
    golden_corpus_sha256: str
    stage_statuses: tuple[PipelineStageStatus, ...]
    integrity_status: str
    integration_status: str
    boundary: IntegrationBoundary

    def __post_init__(self) -> None:
        object.__setattr__(self, "stage_statuses", tuple(self.stage_statuses))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["stage_statuses"] = [asdict(item) for item in self.stage_statuses]
        payload["boundary"] = asdict(self.boundary)
        return payload

