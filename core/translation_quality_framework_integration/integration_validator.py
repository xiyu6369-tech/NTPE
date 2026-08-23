from __future__ import annotations

import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from core.production_runtime.manifest import (
    get_te_v7_artifact_path,
    TE_V71_STAGE113_REVIEW_DEFECTS,
    TE_V71_STAGE113_REVIEW_METRICS,
)
from .integration_model import QualityFrameworkIntegration
from .integrity import verify_quality_framework_integrity
from .references import load_reference, reference_sha256
from .stage_chain import STAGE_CHAIN, STAGE_NAMES, STAGE_PIPELINE_STATUS, validate_stage_chain

SCHEMA_VERSION = "te-v7.1-stage11.7"
INTEGRATION_STATUSES = ("integrated_valid", "integrated_invalid", "insufficient_evidence", "blocked")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
INTEGRATION_ID_PATTERN = re.compile(r"^TQ-INT-[0-9A-F]{20}$")


def derive_integration_status(defects: dict[str, object], metrics: dict[str, object], decision: dict[str, object]) -> str:
    if int(defects.get("blocking_defect_count", 0)) > 0:
        return "blocked"
    metric_rows = metrics.get("metrics", [])
    if any(row.get("status") == "insufficient_evidence" for row in metric_rows):
        return "insufficient_evidence"
    fixture = decision.get("fixture", {})
    if fixture.get("decision", {}).get("decision") != "accepted":
        return "blocked"
    return "integrated_valid"


def validate_quality_framework_integration(record: QualityFrameworkIntegration) -> QualityFrameworkIntegration:
    if INTEGRATION_ID_PATTERN.fullmatch(record.integration_id) is None or not record.source_case_id.strip():
        raise ValueError("quality framework integration identity invalid")
    if record.schema_version != SCHEMA_VERSION:
        raise ValueError("quality framework integration schema version invalid")
    try:
        created = datetime.fromisoformat(record.created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("integration created_at must be ISO 8601") from exc
    if created.tzinfo is None:
        raise ValueError("integration created_at must include a timezone")
    refs = (
        (record.defects_reference, record.defects_sha256), (record.metrics_reference, record.metrics_sha256),
        (record.review_artifact_reference, record.review_artifact_sha256),
        (record.improvement_plan_reference, record.improvement_plan_sha256),
        (record.human_decision_reference, record.human_decision_sha256),
        (record.corpus_governance_reference, record.corpus_governance_sha256),
        (record.golden_corpus_reference, record.golden_corpus_sha256),
    )
    if any(not reference.strip() or SHA256_PATTERN.fullmatch(digest) is None for reference, digest in refs):
        raise ValueError("quality framework reference or SHA-256 invalid")
    validate_stage_chain(tuple(item.stage for item in record.stage_statuses))
    expected_refs = {
        "11.1": (record.defects_reference, record.defects_sha256), "11.2": (record.metrics_reference, record.metrics_sha256),
        "11.3": (record.review_artifact_reference, record.review_artifact_sha256), "11.4": (record.improvement_plan_reference, record.improvement_plan_sha256),
        "11.5": (record.human_decision_reference, record.human_decision_sha256), "11.6": (record.corpus_governance_reference, record.corpus_governance_sha256),
    }
    for item in record.stage_statuses:
        if item.status != STAGE_PIPELINE_STATUS[item.stage] or item.validation_status != "valid" or item.applied:
            raise ValueError("quality framework pipeline stage status invalid")
        if (item.artifact_reference, item.artifact_sha256) != expected_refs[item.stage]:
            raise ValueError("quality framework pipeline reference mismatch")
    if record.integrity_status != "valid" or record.integration_status not in INTEGRATION_STATUSES:
        raise ValueError("quality framework integration status invalid")
    boundary = asdict(record.boundary)
    integer_fields = {"network_requests", "plans_applied", "decisions_applied", "approved_cases_created", "approved_translations_added", "existing_approved_translations_modified"}
    if any(boundary[name] != 0 for name in integer_fields) or any(value is not False for name, value in boundary.items() if name not in integer_fields):
        raise ValueError("quality framework integration boundary must remain inactive")
    return record


def validate_cross_stage_references(record: QualityFrameworkIntegration, *, root: str | Path) -> bool:
    defects = load_reference(root, record.defects_reference)
    metrics = load_reference(root, record.metrics_reference)
    review = load_reference(root, record.review_artifact_reference)
    plan = load_reference(root, record.improvement_plan_reference)
    decision = load_reference(root, record.human_decision_reference)
    governance = load_reference(root, record.corpus_governance_reference)
    if defects.get("stage") != "TE-v7.1-Stage11.1" or metrics.get("stage") != "TE-v7.1-Stage11.2" or review.get("stage") != "TE-v7.1-Stage11.3" or plan.get("stage") != "TE-v7.1-Stage11.4" or decision.get("stage") != "TE-v7.1-Stage11.5" or governance.get("stage") != "TE-v7.1-Stage11.6":
        raise ValueError("cross-stage artifact order or identity invalid")
    defect_ids = {row["defect_id"] for row in defects["defects"]}
    overall = next(row for row in metrics["metrics"] if row["dimension"] == "overall")
    if overall["evidence_count"] != defects["defect_count"] or overall["blocking_defect_count"] != defects["blocking_defect_count"]:
        raise ValueError("Stage 11.1 to 11.2 defect evidence mismatch")
    review_defects_ref = str(get_te_v7_artifact_path(root, "te_v71_stage113", TE_V71_STAGE113_REVIEW_DEFECTS))
    review_metrics_ref = str(get_te_v7_artifact_path(root, "te_v71_stage113", TE_V71_STAGE113_REVIEW_METRICS))
    review_defects = load_reference(root, review_defects_ref)
    review_metrics = load_reference(root, review_metrics_ref)
    if review_defects["defects_artifact"] != record.defects_reference or set(review_defects["defect_ids"]) != defect_ids:
        raise ValueError("Stage 11.2 to 11.3 defect reference mismatch")
    if review_metrics["metrics_artifact"] != record.metrics_reference or review_metrics["overall_score"] != overall["score"]:
        raise ValueError("Stage 11.2 to 11.3 metrics reference mismatch")
    if review["defect_count"] != defects["defect_count"] or review["blocking_defect_count"] != defects["blocking_defect_count"] or review["quality_pass"] is not False:
        raise ValueError("Stage 11.3 review evidence mismatch")
    planned_ids = {defect_id for row in plan["plans"] for defect_id in row["related_defect_ids"]}
    if planned_ids != defect_ids or plan["plans_applied"] != 0 or any(row["implementation_status"] != "planned_not_applied" for row in plan["plans"]):
        raise ValueError("Stage 11.3 to 11.4 plan evidence mismatch")
    fixture = decision.get("fixture", {})
    decision_value = fixture.get("decision", {})
    decision_refs = decision.get("integrity_references", {})
    if not fixture.get("not_applied") or decision_value.get("decision_source") != "human_review":
        raise ValueError("Stage 11.5 decision must remain human-only and not applied")
    if decision_refs != {
        "review_artifact_sha256": record.review_artifact_sha256,
        "metrics_sha256": reference_sha256(root, review_metrics_ref),
        "defects_sha256": reference_sha256(root, review_defects_ref),
    }:
        raise ValueError("Stage 11.4 to 11.5 decision integrity mismatch")
    human_policy = governance.get("human_only_approval_policy", {})
    corpus_summary = governance.get("current_corpus_summary", {})
    if human_policy.get("accepted_decision_is_approval") is not False or human_policy.get("automatic_approval") is not False:
        raise ValueError("Stage 11.5 to 11.6 governance prerequisite mismatch")
    if corpus_summary.get("approved_cases") != 0 or corpus_summary.get("approved_translations") != 0 or not corpus_summary.get("all_existing_approved_final_translation_null"):
        raise ValueError("Stage 11.6 corpus state mismatch")
    upstream = governance.get("integrity", {})
    expected_upstream = {
        "stage111_defects_sha256": record.defects_sha256, "stage112_metrics_sha256": record.metrics_sha256,
        "stage113_review_sha256": record.review_artifact_sha256, "stage114_plan_sha256": record.improvement_plan_sha256,
        "stage115_decision_contract_sha256": record.human_decision_sha256, "golden_corpus_sha256": record.golden_corpus_sha256,
    }
    if any(upstream.get(name) != digest for name, digest in expected_upstream.items()):
        raise ValueError("Stage 11.6 upstream integrity chain mismatch")
    return True


def validate_complete_integration(record: QualityFrameworkIntegration, *, root: str | Path) -> QualityFrameworkIntegration:
    validate_quality_framework_integration(record)
    integrity = verify_quality_framework_integrity(record, root=root)
    if not integrity.valid:
        raise ValueError(f"quality framework integrity failed at {integrity.failed_stage}: {integrity.failed_reference}")
    validate_cross_stage_references(record, root=root)
    return record

