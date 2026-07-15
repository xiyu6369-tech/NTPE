from __future__ import annotations

import hashlib
from pathlib import Path

from .integration_model import IntegrationBoundary, PipelineStageStatus, QualityFrameworkIntegration
from .integration_validator import SCHEMA_VERSION, derive_integration_status, validate_complete_integration
from .references import load_reference, reference_sha256
from .stage_chain import STAGE_CHAIN, STAGE_PIPELINE_STATUS


def build_quality_framework_integration(
    *,
    root: str | Path,
    source_case_id: str,
    created_at: str,
    defects_reference: str,
    metrics_reference: str,
    review_artifact_reference: str,
    improvement_plan_reference: str,
    human_decision_reference: str,
    corpus_governance_reference: str,
    golden_corpus_reference: str,
) -> QualityFrameworkIntegration:
    references = {
        "11.1": defects_reference, "11.2": metrics_reference, "11.3": review_artifact_reference,
        "11.4": improvement_plan_reference, "11.5": human_decision_reference, "11.6": corpus_governance_reference,
    }
    hashes = {stage: reference_sha256(root, reference) for stage, reference in references.items()}
    golden_hash = reference_sha256(root, golden_corpus_reference)
    identity_material = "\n".join((source_case_id, created_at, *(hashes[stage] for stage in STAGE_CHAIN), golden_hash))
    integration_id = "TQ-INT-" + hashlib.sha256(identity_material.encode("utf-8")).hexdigest()[:20].upper()
    statuses = tuple(PipelineStageStatus(stage, STAGE_PIPELINE_STATUS[stage], references[stage], hashes[stage], "valid", False) for stage in STAGE_CHAIN)
    integration_status = derive_integration_status(load_reference(root, defects_reference), load_reference(root, metrics_reference), load_reference(root, human_decision_reference))
    record = QualityFrameworkIntegration(
        integration_id, SCHEMA_VERSION, created_at, source_case_id,
        defects_reference, hashes["11.1"], metrics_reference, hashes["11.2"],
        review_artifact_reference, hashes["11.3"], improvement_plan_reference, hashes["11.4"],
        human_decision_reference, hashes["11.5"], corpus_governance_reference, hashes["11.6"],
        golden_corpus_reference, golden_hash, statuses, "valid", integration_status, IntegrationBoundary(),
    )
    return validate_complete_integration(record, root=root)

