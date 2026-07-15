from __future__ import annotations

import json
from collections.abc import Mapping

from .integration_model import IntegrationBoundary, PipelineStageStatus, QualityFrameworkIntegration
from .integration_validator import validate_quality_framework_integration


def serialize_quality_framework_integration(record: QualityFrameworkIntegration) -> str:
    validate_quality_framework_integration(record)
    return json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def deserialize_quality_framework_integration(payload: str | bytes | Mapping[str, object]) -> QualityFrameworkIntegration:
    raw = json.loads(payload) if isinstance(payload, (str, bytes, bytearray)) else dict(payload)
    required = {"integration_id", "schema_version", "created_at", "source_case_id", "defects_reference", "defects_sha256", "metrics_reference", "metrics_sha256", "review_artifact_reference", "review_artifact_sha256", "improvement_plan_reference", "improvement_plan_sha256", "human_decision_reference", "human_decision_sha256", "corpus_governance_reference", "corpus_governance_sha256", "golden_corpus_reference", "golden_corpus_sha256", "stage_statuses", "integrity_status", "integration_status", "boundary"}
    if set(raw) != required:
        raise ValueError("quality framework integration schema fields invalid")
    try:
        stages = tuple(PipelineStageStatus(**item) for item in raw.pop("stage_statuses"))
        boundary = IntegrationBoundary(**raw.pop("boundary"))
        record = QualityFrameworkIntegration(stage_statuses=stages, boundary=boundary, **raw)
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("quality framework integration payload invalid") from exc
    return validate_quality_framework_integration(record)

