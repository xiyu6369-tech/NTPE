from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.translation_quality_review_decision import (
    ALLOWED_DECISIONS, DECISION_SOURCE, SCHEMA_VERSION, ReviewerProvenance,
    ReviewDecisionStatus, build_review_decision, deserialize_review_decision,
    file_sha256, serialize_review_decision, validate_review_decision,
    verify_review_decision_integrity,
)
from core.translation_quality_corpus import load_golden_corpus
from core.translation_prompt_improvement_planner import verify_improvement_plan_artifact

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/te_v71_quality_framework"
REVIEW = FIXTURES / "TE_V71_STAGE113_REVIEW.json"
METRICS = FIXTURES / "TE_V71_STAGE112_QUALITY_METRICS.json"
DEFECTS = FIXTURES / "TE_V71_STAGE111_TRANSLATION_DEFECTS.json"
ARTIFACT = FIXTURES / "TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json"
CORPUS = ROOT / "archive/historical/quality_corpus/golden_review/te_v71_initial_defects.json"
PLAN = FIXTURES / "TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json"


def _decision(status: str = "accepted"):
    return build_review_decision(
        review_id="TE-V71-STAGE113-REVIEW-001", decision=status,
        reviewer=ReviewerProvenance("human-reviewer-001", "Human Reviewer"),
        created_at="2026-07-15T00:00:00+08:00",
        decision_reason=f"Human reviewer records {status} after examining the redacted evidence package.",
        review_artifact_sha256=file_sha256(REVIEW), metrics_sha256=file_sha256(METRICS),
        defects_sha256=file_sha256(DEFECTS),
    )


@pytest.mark.parametrize("status", ALLOWED_DECISIONS)
def test_all_and_only_supported_decisions_build(status: str) -> None:
    assert _decision(status).decision.value == status


def test_unknown_decision_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        _decision("auto_approved")


def test_decision_source_is_human_only() -> None:
    assert _decision().decision_source == DECISION_SOURCE == "human_review"


@pytest.mark.parametrize("source", ["provider", "runtime", "planner", "metrics", "quality_engine", "automatic", "system", "model", "llm"])
def test_automatic_sources_rejected(source: str) -> None:
    with pytest.raises(ValueError, match="human_review"):
        validate_review_decision(replace(_decision(), decision_source=source))


@pytest.mark.parametrize("identity", ["system", "automatic-reviewer", "provider", "runtime agent", "planner", "metrics", "model", "llm"])
def test_automatic_reviewer_identity_rejected(identity: str) -> None:
    with pytest.raises(ValueError, match="human reviewer"):
        validate_review_decision(replace(_decision(), reviewer=ReviewerProvenance(identity, identity)))


def test_missing_reviewer_rejected() -> None:
    with pytest.raises(ValueError, match="human reviewer"):
        validate_review_decision(replace(_decision(), reviewer=ReviewerProvenance("", "")))


@pytest.mark.parametrize("reason", ["", "OK", "PASS", "accepted"])
def test_non_substantive_reason_rejected(reason: str) -> None:
    with pytest.raises(ValueError, match="substantive"):
        validate_review_decision(replace(_decision(), decision_reason=reason))


def test_review_id_is_required() -> None:
    with pytest.raises(ValueError, match="identifiers"):
        validate_review_decision(replace(_decision(), review_id=""))


@pytest.mark.parametrize("field", ["review_artifact_sha256", "metrics_sha256", "defects_sha256"])
def test_invalid_sha256_rejected(field: str) -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        validate_review_decision(replace(_decision(), **{field: "0" * 63}))


def test_referenced_artifact_integrity_passes() -> None:
    assert verify_review_decision_integrity(_decision(), {
        "review_artifact_sha256": REVIEW, "metrics_sha256": METRICS, "defects_sha256": DEFECTS,
    })


def test_tampered_reference_rejected(tmp_path: Path) -> None:
    tampered = tmp_path / "review.json"
    tampered.write_bytes(REVIEW.read_bytes() + b" ")
    with pytest.raises(ValueError, match="mismatch"):
        verify_review_decision_integrity(_decision(), {
            "review_artifact_sha256": tampered, "metrics_sha256": METRICS, "defects_sha256": DEFECTS,
        })


def test_serialization_round_trip_is_canonical_and_deterministic() -> None:
    encoded = serialize_review_decision(_decision())
    assert serialize_review_decision(deserialize_review_decision(encoded)) == encoded
    assert encoded == serialize_review_decision(_decision())


def test_schema_version_and_created_at_are_fixed_and_valid() -> None:
    decision = _decision()
    assert decision.schema_version == SCHEMA_VERSION == "te-v7.1-stage11.5"
    assert decision.created_at.endswith("+08:00")


def test_naive_created_at_rejected() -> None:
    with pytest.raises(ValueError, match="timezone"):
        validate_review_decision(replace(_decision(), created_at="2026-07-15T00:00:00"))


def test_stage_artifact_fixture_is_canonical_and_not_applied() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    fixture = payload["fixture"]
    assert fixture["fixture"] and fixture["test_only"] and fixture["example"] and fixture["not_applied"]
    encoded = serialize_review_decision(deserialize_review_decision(fixture["decision"]))
    assert hashlib.sha256(encoded.encode("utf-8")).hexdigest() == fixture["decision_payload_sha256"]


def test_stage_artifact_integrity_references_match() -> None:
    refs = json.loads(ARTIFACT.read_text(encoding="utf-8"))["integrity_references"]
    assert refs == {"review_artifact_sha256": file_sha256(REVIEW), "metrics_sha256": file_sha256(METRICS), "defects_sha256": file_sha256(DEFECTS)}


def test_previous_artifacts_are_not_mutated_or_applied() -> None:
    assert all(case.approved_final_translation is None for case in load_golden_corpus(CORPUS))
    plan = verify_improvement_plan_artifact(PLAN)
    assert plan["plans_applied"] == 0 and all(row["implementation_status"] == "planned_not_applied" for row in plan["plans"])


def test_execution_and_stage116_boundaries_are_closed() -> None:
    boundary = json.loads(ARTIFACT.read_text(encoding="utf-8"))["boundary"]
    false_fields = [key for key, value in boundary.items() if key not in {"plans_applied", "network_requests"}]
    assert all(boundary[key] is False for key in false_fields)
    assert boundary["plans_applied"] == 0 and boundary["network_requests"] == 0


def test_accepted_is_explicit_input_not_metric_inference() -> None:
    assert _decision("accepted").decision is ReviewDecisionStatus.ACCEPTED
    assert _decision("insufficient_evidence").decision is ReviewDecisionStatus.INSUFFICIENT_EVIDENCE
