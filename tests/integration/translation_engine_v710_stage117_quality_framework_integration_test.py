from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

import core.translation_quality_framework_integration as framework
from core.translation_quality_corpus import load_golden_corpus
from core.translation_quality_framework_integration import (
    IntegrationBoundary, PipelineStageStatus, STAGE_CHAIN, build_quality_framework_integration,
    derive_integration_status, deserialize_quality_framework_integration,
    reference_sha256, serialize_quality_framework_integration,
    validate_complete_integration, validate_cross_stage_references,
    validate_quality_framework_integration, validate_stage_chain,
    verify_quality_framework_integrity,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/te_v71_quality_framework"
DEFECTS = "tests/fixtures/te_v71_quality_framework/TE_V71_STAGE111_TRANSLATION_DEFECTS.json"
METRICS = "tests/fixtures/te_v71_quality_framework/TE_V71_STAGE112_QUALITY_METRICS.json"
REVIEW = "tests/fixtures/te_v71_quality_framework/TE_V71_STAGE113_REVIEW.json"
PLAN = "tests/fixtures/te_v71_quality_framework/TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json"
DECISION = "tests/fixtures/te_v71_quality_framework/TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json"
GOVERNANCE = "tests/fixtures/te_v71_quality_framework/TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json"
CORPUS = "archive/historical/quality_corpus/golden_review/te_v71_initial_defects.json"
ARTIFACT = FIXTURES / "TE_V71_STAGE117_QUALITY_FRAMEWORK_INTEGRATION.json"


def _record():
    return build_quality_framework_integration(
        root=ROOT, source_case_id="TQ-DEF-B", created_at="2026-07-15T02:00:00+08:00",
        defects_reference=DEFECTS, metrics_reference=METRICS, review_artifact_reference=REVIEW,
        improvement_plan_reference=PLAN, human_decision_reference=DECISION,
        corpus_governance_reference=GOVERNANCE, golden_corpus_reference=CORPUS,
    )


def _load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_stage_chain_is_exact_and_valid() -> None:
    assert STAGE_CHAIN == ("11.1", "11.2", "11.3", "11.4", "11.5", "11.6")
    assert validate_stage_chain(STAGE_CHAIN)


@pytest.mark.parametrize("chain", [
    ("11.1", "11.2", "11.3", "11.4", "11.6"),
    ("11.1", "11.2", "11.3", "11.5", "11.4", "11.6"),
    ("11.1", "11.2", "11.3", "11.4", "11.5", "11.5"),
    ("11.1", "11.2", "11.3", "11.4", "11.5", "11.6", "11.8"),
    ("11.1", "runtime", "11.2", "11.3", "11.4", "11.5", "11.6"),
    ("11.1", "provider", "11.2", "11.3", "11.4", "11.5", "11.6"),
])
def test_invalid_stage_chain_fails_closed(chain: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="exactly"):
        validate_stage_chain(chain)


def test_model_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        _record().integration_status = "integrated_valid"


def test_integration_id_is_deterministic() -> None:
    assert _record().integration_id == "TQ-INT-01D295CF6F415BBBCD31"
    assert _record() == _record()


def test_canonical_serialization_round_trip() -> None:
    encoded = serialize_quality_framework_integration(_record())
    assert serialize_quality_framework_integration(deserialize_quality_framework_integration(encoded)) == encoded
    assert encoded == serialize_quality_framework_integration(_record())


@pytest.mark.parametrize("field,reference", [
    ("defects_sha256", DEFECTS), ("metrics_sha256", METRICS),
    ("review_artifact_sha256", REVIEW), ("improvement_plan_sha256", PLAN),
    ("human_decision_sha256", DECISION), ("corpus_governance_sha256", GOVERNANCE),
    ("golden_corpus_sha256", CORPUS),
])
def test_each_reference_sha_matches_disk(field: str, reference: str) -> None:
    assert getattr(_record(), field) == reference_sha256(ROOT, reference)


def test_all_references_exist() -> None:
    record = _record()
    references = [record.defects_reference, record.metrics_reference, record.review_artifact_reference, record.improvement_plan_reference, record.human_decision_reference, record.corpus_governance_reference, record.golden_corpus_reference]
    assert all((ROOT / reference).is_file() for reference in references)


def test_integrity_result_is_structured_and_valid() -> None:
    result = verify_quality_framework_integrity(_record(), root=ROOT)
    assert result.valid and result.failed_stage is None and result.failed_reference is None


def test_tampered_sha_reports_failed_stage() -> None:
    record = replace(_record(), metrics_sha256="0" * 64)
    result = verify_quality_framework_integrity(record, root=ROOT)
    assert not result.valid and result.failed_stage == "11.2"
    assert result.failed_reference == METRICS and result.expected_sha256 == "0" * 64


def test_missing_artifact_reports_failed_reference() -> None:
    record = replace(_record(), human_decision_reference="artifacts/missing-decision.json")
    stages = tuple(replace(item, artifact_reference=record.human_decision_reference) if item.stage == "11.5" else item for item in record.stage_statuses)
    record = replace(record, stage_statuses=stages)
    result = verify_quality_framework_integrity(record, root=ROOT)
    assert not result.valid and result.failed_stage == "11.5" and result.actual_sha256 is None


def test_complete_validation_fails_on_integrity_mismatch() -> None:
    record = replace(_record(), defects_sha256="f" * 64)
    stages = tuple(replace(item, artifact_sha256="f" * 64) if item.stage == "11.1" else item for item in record.stage_statuses)
    with pytest.raises(ValueError, match="11.1"):
        validate_complete_integration(replace(record, stage_statuses=stages), root=ROOT)


def test_cross_stage_references_are_valid() -> None:
    assert validate_cross_stage_references(_record(), root=ROOT)


def test_defects_and_metrics_counts_align() -> None:
    defects, metrics = _load(DEFECTS), _load(METRICS)
    overall = next(row for row in metrics["metrics"] if row["dimension"] == "overall")
    assert overall["evidence_count"] == defects["defect_count"] == 6
    assert overall["blocking_defect_count"] == defects["blocking_defect_count"] == 1


def test_review_references_defects_and_metrics() -> None:
    review_defects = _load("artifacts/te_v71_stage113/TE_V71_STAGE113_REVIEW_DEFECTS.json")
    review_metrics = _load("artifacts/te_v71_stage113/TE_V71_STAGE113_REVIEW_METRICS.json")
    assert review_defects["defects_artifact"] == DEFECTS
    assert review_metrics["metrics_artifact"] == METRICS


def test_improvement_plans_remain_not_applied() -> None:
    plan = _load(PLAN)
    assert plan["plans_applied"] == 0
    assert all(row["implementation_status"] == "planned_not_applied" for row in plan["plans"])


def test_human_decision_remains_human_only_and_not_applied() -> None:
    decision = _load(DECISION)
    assert decision["fixture"]["decision"]["decision_source"] == "human_review"
    assert decision["fixture"]["not_applied"] and decision["boundary"]["decision_applied"] is False


def test_accepted_decision_is_not_corpus_approval() -> None:
    decision, governance = _load(DECISION), _load(GOVERNANCE)
    assert decision["fixture"]["decision"]["decision"] == "accepted"
    assert governance["human_only_approval_policy"]["accepted_decision_is_approval"] is False
    assert governance["current_corpus_summary"]["approved_cases"] == 0


def test_governance_has_no_approved_translation() -> None:
    governance = _load(GOVERNANCE)
    assert governance["current_corpus_summary"]["approved_translations"] == 0
    assert governance["fixture"]["approved_final_translation"] is None


def test_golden_corpus_is_unchanged() -> None:
    cases = load_golden_corpus(ROOT / CORPUS)
    assert len(cases) == 6 and all(case.approved_final_translation is None for case in cases)
    assert _record().golden_corpus_sha256 == "4a06d256d900c8bb7706098fd79f2d53889d469e9b62516d81334ef34433f2cc"


def test_blocking_defect_forces_blocked_status() -> None:
    assert _record().integration_status == "blocked"
    assert derive_integration_status(_load(DEFECTS), _load(METRICS), _load(DECISION)) == "blocked"


def test_insufficient_evidence_is_not_integrated_valid() -> None:
    defects = {"blocking_defect_count": 0}
    metrics = {"metrics": [{"status": "insufficient_evidence"}]}
    decision = {"fixture": {"decision": {"decision": "accepted"}}}
    assert derive_integration_status(defects, metrics, decision) == "insufficient_evidence"


def test_integrated_valid_does_not_claim_approval() -> None:
    defects = {"blocking_defect_count": 0}
    metrics = {"metrics": [{"status": "evaluated"}]}
    decision = {"fixture": {"decision": {"decision": "accepted"}}}
    assert derive_integration_status(defects, metrics, decision) == "integrated_valid"
    assert _record().boundary.approved_translations_added == 0


def test_nonaccepted_decision_blocks_eligibility() -> None:
    defects = {"blocking_defect_count": 0}
    metrics = {"metrics": [{"status": "evaluated"}]}
    decision = {"fixture": {"decision": {"decision": "needs_revision"}}}
    assert derive_integration_status(defects, metrics, decision) == "blocked"


def test_pipeline_statuses_are_descriptive_and_not_applied() -> None:
    statuses = {item.stage: item.status for item in _record().stage_statuses}
    assert statuses == {"11.1": "recorded", "11.2": "calculated", "11.3": "created", "11.4": "not_applied", "11.5": "not_applied", "11.6": "not_applied"}
    assert all(not item.applied and item.validation_status == "valid" for item in _record().stage_statuses)


def test_boundary_is_fully_inactive() -> None:
    boundary = _record().boundary
    assert boundary.network_requests == boundary.plans_applied == boundary.decisions_applied == 0
    assert boundary.approved_cases_created == boundary.approved_translations_added == 0
    assert not boundary.provider_executed and not boundary.runtime_executed and not boundary.prompt_modified
    assert not boundary.translation_quality_improved and not boundary.stage118_started


def test_active_boundary_rejected() -> None:
    with pytest.raises(ValueError, match="inactive"):
        validate_quality_framework_integration(replace(_record(), boundary=replace(IntegrationBoundary(), network_requests=1)))


def test_invalid_pipeline_applied_flag_rejected() -> None:
    stages = list(_record().stage_statuses); stages[3] = replace(stages[3], applied=True)
    with pytest.raises(ValueError, match="stage status"):
        validate_quality_framework_integration(replace(_record(), stage_statuses=tuple(stages)))


def test_integration_exposes_no_mutating_actions() -> None:
    for name in ("apply_plan", "apply_decision", "approve_corpus", "execute_provider", "execute_runtime"):
        assert not hasattr(framework, name)


def test_stage_artifact_matches_record_and_is_not_applied() -> None:
    artifact, record = json.loads(ARTIFACT.read_text(encoding="utf-8")), _record()
    contract = artifact["integration_contract"]
    assert contract["integration_id"] == record.integration_id and contract["integration_status"] == record.integration_status
    assert contract["fixture"] and contract["test_only"] and contract["example"] and contract["not_applied"]


def test_stage_artifact_integrity_chain_matches_record() -> None:
    chain, record = json.loads(ARTIFACT.read_text(encoding="utf-8"))["integrity_chain"], _record()
    for field, value in chain.items():
        assert getattr(record, field) == value


def test_stage_artifact_makes_no_quality_or_release_claim() -> None:
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert artifact["blocking_summary"]["quality_pass"] is False
    assert artifact["validation_summary"]["quality_claimed"] is False
    assert artifact["validation_summary"]["release_ready_claimed"] is False


def test_validator_accepts_complete_record() -> None:
    assert validate_quality_framework_integration(_record()) == _record()


def test_schema_version_is_fixed() -> None:
    assert _record().schema_version == "te-v7.1-stage11.7"


def test_created_at_requires_timezone() -> None:
    with pytest.raises(ValueError, match="timezone"):
        validate_quality_framework_integration(replace(_record(), created_at="2026-07-15T02:00:00"))
