from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

import core.translation_quality_corpus_governance as governance
from core.translation_quality_corpus import load_golden_corpus
from core.translation_quality_corpus_governance import (
    ALLOWED_TRANSITIONS, APPROVAL_SOURCE, CorpusLifecycle, approve_corpus_case,
    build_governance_record, create_case_revision, deprecate_corpus_case,
    deserialize_governance_record, reject_corpus_case, serialize_governance_record,
    sha256_file, sha256_text, submit_corpus_case_for_review, supersede_corpus_case,
    validate_governance_record, validate_lifecycle_transition, verify_corpus_integrity,
)
from core.translation_quality_review_decision import ReviewDecisionStatus, deserialize_review_decision

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/te_v71_quality_framework"
CORPUS = ROOT / "archive/historical/quality_corpus/golden_review/te_v71_initial_defects.json"
STAGE115 = FIXTURES / "TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json"
REVIEW = FIXTURES / "TE_V71_STAGE113_REVIEW.json"
METRICS = FIXTURES / "TE_V71_STAGE112_QUALITY_METRICS.json"
DEFECTS = FIXTURES / "TE_V71_STAGE111_TRANSLATION_DEFECTS.json"
ARTIFACT = FIXTURES / "TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json"
SOURCE_TEXT = "isolated governance source evidence"


def _decision():
    return deserialize_review_decision(json.loads(STAGE115.read_text(encoding="utf-8"))["fixture"]["decision"])


def _decision_artifacts() -> dict[str, str]:
    return {"review_artifact_sha256": str(REVIEW), "metrics_sha256": str(METRICS), "defects_sha256": str(DEFECTS)}


def _draft(case_id: str = "TQ-GOV-CASE-001"):
    return build_governance_record(
        case_id=case_id, source_text_excerpt="[redacted governance evidence]",
        source_language="ko", target_language="zh-Hant", source_text_sha256=sha256_text(SOURCE_TEXT),
        source_artifact_reference="quality_corpus/golden_review/te_v71_initial_defects.json",
        source_artifact_sha256=sha256_file(CORPUS), created_at="2026-07-15T01:00:00+08:00",
        created_by="human-governor-001", creation_reason="Create an isolated governance test fixture.",
    )


def _reviewed(case_id: str = "TQ-GOV-CASE-001"):
    return submit_corpus_case_for_review(_draft(case_id), reviewer="human-reviewer-002", reason="Submit immutable evidence for independent human review.", submitted_at="2026-07-15T01:05:00+08:00")


def _approved(case_id: str = "TQ-GOV-CASE-001"):
    return approve_corpus_case(
        _reviewed(case_id), approved_final_translation="經人工治理核准的測試譯文。", source_text=SOURCE_TEXT,
        human_approver="human-governor-003", approval_reason="Approve this isolated fixture after a separate governance review.",
        approved_at="2026-07-15T01:10:00+08:00", approval_source=APPROVAL_SOURCE,
        decision=_decision(), source_artifact=str(CORPUS), decision_artifacts=_decision_artifacts(),
    )


@pytest.mark.parametrize("status", [item.value for item in CorpusLifecycle])
def test_lifecycle_contract_contains_exact_statuses(status: str) -> None:
    assert CorpusLifecycle(status).value == status


@pytest.mark.parametrize("source,target", [(source.value, target.value) for source, targets in ALLOWED_TRANSITIONS.items() for target in targets])
def test_allowed_transitions_pass(source: str, target: str) -> None:
    assert validate_lifecycle_transition(source, target)


@pytest.mark.parametrize("source,target", [("draft", "approved"), ("rejected", "approved"), ("deprecated", "approved"), ("superseded", "approved")])
def test_forbidden_transitions_fail_closed(source: str, target: str) -> None:
    with pytest.raises(ValueError, match="invalid"):
        validate_lifecycle_transition(source, target)


def test_draft_cannot_be_approved_directly() -> None:
    with pytest.raises(ValueError, match="invalid"):
        approve_corpus_case(_draft(), approved_final_translation="核准譯文", source_text=SOURCE_TEXT, human_approver="human-governor-003", approval_reason="Attempt a prohibited direct draft approval.", approved_at="2026-07-15T01:10:00+08:00", approval_source=APPROVAL_SOURCE, decision=_decision(), source_artifact=str(CORPUS), decision_artifacts=_decision_artifacts())


@pytest.mark.parametrize("status", [ReviewDecisionStatus.REJECTED, ReviewDecisionStatus.NEEDS_REVISION, ReviewDecisionStatus.INSUFFICIENT_EVIDENCE])
def test_only_accepted_decision_is_approval_prerequisite(status: ReviewDecisionStatus) -> None:
    with pytest.raises(ValueError, match="accepted"):
        approve_corpus_case(_reviewed(), approved_final_translation="核准譯文", source_text=SOURCE_TEXT, human_approver="human-governor-003", approval_reason="Reject non-accepted decision evidence from governance approval.", approved_at="2026-07-15T01:10:00+08:00", approval_source=APPROVAL_SOURCE, decision=replace(_decision(), decision=status), source_artifact=str(CORPUS), decision_artifacts=_decision_artifacts())


@pytest.mark.parametrize("actor", ["provider", "runtime agent", "planner", "metrics", "quality_engine", "automatic", "system", "model", "llm", "benchmark", "comparison"])
def test_automatic_approver_is_rejected(actor: str) -> None:
    with pytest.raises(ValueError, match="human provenance"):
        approve_corpus_case(_reviewed(), approved_final_translation="核准譯文", source_text=SOURCE_TEXT, human_approver=actor, approval_reason="Automated identities cannot approve Golden Corpus content.", approved_at="2026-07-15T01:10:00+08:00", approval_source=APPROVAL_SOURCE, decision=_decision(), source_artifact=str(CORPUS), decision_artifacts=_decision_artifacts())


def test_wrong_approval_source_rejected() -> None:
    with pytest.raises(ValueError, match="human_governance_review"):
        approve_corpus_case(_reviewed(), approved_final_translation="核准譯文", source_text=SOURCE_TEXT, human_approver="human-governor-003", approval_reason="Reject an invalid approval source at the governance boundary.", approved_at="2026-07-15T01:10:00+08:00", approval_source="human_review", decision=_decision(), source_artifact=str(CORPUS), decision_artifacts=_decision_artifacts())


@pytest.mark.parametrize("translation", ["", "   "])
def test_empty_approved_translation_rejected(translation: str) -> None:
    with pytest.raises(ValueError, match="translation is required"):
        approve_corpus_case(_reviewed(), approved_final_translation=translation, source_text=SOURCE_TEXT, human_approver="human-governor-003", approval_reason="Reject an empty proposed approved translation value.", approved_at="2026-07-15T01:10:00+08:00", approval_source=APPROVAL_SOURCE, decision=_decision(), source_artifact=str(CORPUS), decision_artifacts=_decision_artifacts())


def test_source_text_cannot_be_used_as_translation() -> None:
    with pytest.raises(ValueError, match="differ"):
        approve_corpus_case(_reviewed(), approved_final_translation=SOURCE_TEXT, source_text=SOURCE_TEXT, human_approver="human-governor-003", approval_reason="Reject copying source text into the approved translation field.", approved_at="2026-07-15T01:10:00+08:00", approval_source=APPROVAL_SOURCE, decision=_decision(), source_artifact=str(CORPUS), decision_artifacts=_decision_artifacts())


def test_source_integrity_mismatch_rejected() -> None:
    with pytest.raises(ValueError, match="source text integrity"):
        approve_corpus_case(_reviewed(), approved_final_translation="核准譯文", source_text="tampered source", human_approver="human-governor-003", approval_reason="Reject mismatched immutable source evidence during approval.", approved_at="2026-07-15T01:10:00+08:00", approval_source=APPROVAL_SOURCE, decision=_decision(), source_artifact=str(CORPUS), decision_artifacts=_decision_artifacts())


def test_decision_integrity_mismatch_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "review.json"; bad.write_bytes(REVIEW.read_bytes() + b" ")
    refs = _decision_artifacts(); refs["review_artifact_sha256"] = str(bad)
    with pytest.raises(ValueError, match="integrity mismatch"):
        approve_corpus_case(_reviewed(), approved_final_translation="核准譯文", source_text=SOURCE_TEXT, human_approver="human-governor-003", approval_reason="Reject tampered decision evidence during governance approval.", approved_at="2026-07-15T01:10:00+08:00", approval_source=APPROVAL_SOURCE, decision=_decision(), source_artifact=str(CORPUS), decision_artifacts=refs)


def test_explicit_approval_records_complete_provenance() -> None:
    record = _approved()
    assert record.status is CorpusLifecycle.APPROVED and record.approved_final_translation
    assert record.approval is not None and record.approval.approval_source == APPROVAL_SOURCE
    assert record.approval.approval_decision_id == _decision().decision_id
    assert record.approval.approved_translation_sha256 == sha256_text(record.approved_final_translation)


def test_unapproved_lifecycle_retains_null_translation() -> None:
    assert _draft().approved_final_translation is None
    assert _reviewed().approved_final_translation is None


def test_records_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        _draft().status = CorpusLifecycle.APPROVED


def test_revision_is_append_only_and_increasing() -> None:
    original = _approved()
    revised = create_case_revision(original, changed_by="human-editor-004", change_reason="Create a new revision without mutating approved history.", changed_at="2026-07-15T01:20:00+08:00")
    assert revised.revision_number == 2 and revised.previous_revision_id == original.revision_id
    assert revised.status is CorpusLifecycle.DRAFT and revised.approved_final_translation is None
    assert original.status is CorpusLifecycle.APPROVED and original.approved_final_translation is not None


def test_supersession_requires_different_approved_target() -> None:
    first, second = _approved("CASE-A"), _approved("CASE-B")
    superseded = supersede_corpus_case(first, superseded_by=second, human_approver="human-governor-005", supersession_reason="Replace the older approved case with a separately approved case.", superseded_at="2026-07-15T01:30:00+08:00")
    assert superseded.status is CorpusLifecycle.SUPERSEDED and superseded.supersession.superseded_by_case_id == "CASE-B"
    assert second.status is CorpusLifecycle.APPROVED


def test_self_supersession_rejected() -> None:
    record = _approved("CASE-A")
    with pytest.raises(ValueError, match="different approved"):
        supersede_corpus_case(record, superseded_by=record, human_approver="human-governor-005", supersession_reason="Reject an invalid self supersession request.", superseded_at="2026-07-15T01:30:00+08:00")


def test_deprecation_requires_approved_or_superseded() -> None:
    deprecated = deprecate_corpus_case(_approved(), deprecated_by="human-governor-006", deprecation_reason="Retire this approved fixture while preserving its audit history.", deprecated_at="2026-07-15T01:40:00+08:00")
    assert deprecated.status is CorpusLifecycle.DEPRECATED and deprecated.deprecation is not None
    with pytest.raises(ValueError, match="invalid"):
        deprecate_corpus_case(_draft(), deprecated_by="human-governor-006", deprecation_reason="Reject deprecation from an unapproved draft lifecycle.", deprecated_at="2026-07-15T01:40:00+08:00")


def test_rejected_case_has_null_translation_and_cannot_approve() -> None:
    rejected = reject_corpus_case(_reviewed(), rejected_by="human-reviewer-007", rejection_reason="Reject this fixture after independent governance review.", rejected_at="2026-07-15T01:50:00+08:00")
    assert rejected.status is CorpusLifecycle.REJECTED and rejected.approved_final_translation is None
    with pytest.raises(ValueError, match="invalid"):
        approve_corpus_case(rejected, approved_final_translation="核准譯文", source_text=SOURCE_TEXT, human_approver="human-governor-003", approval_reason="Rejected cases cannot be directly approved later.", approved_at="2026-07-15T02:00:00+08:00", approval_source=APPROVAL_SOURCE, decision=_decision(), source_artifact=str(CORPUS), decision_artifacts=_decision_artifacts())


def test_canonical_serialization_round_trip() -> None:
    encoded = serialize_governance_record(_approved())
    assert serialize_governance_record(deserialize_governance_record(encoded)) == encoded
    assert encoded == serialize_governance_record(_approved())


def test_existing_corpus_remains_unapproved_and_unchanged() -> None:
    cases = load_golden_corpus(CORPUS)
    assert len(cases) == 6 and all(case.approved_final_translation is None for case in cases)
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert artifact["integrity"]["golden_corpus_sha256"] == sha256_file(CORPUS)


def test_stage115_fixture_does_not_approve_corpus() -> None:
    prior = json.loads(STAGE115.read_text(encoding="utf-8"))
    current = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert prior["fixture"]["not_applied"] is True
    assert current["current_corpus_summary"]["approved_cases"] == 0
    assert current["boundary"]["approved_translations_added"] == 0


def test_stage_artifact_fixture_is_not_applied() -> None:
    fixture = json.loads(ARTIFACT.read_text(encoding="utf-8"))["fixture"]
    assert fixture["fixture"] and fixture["test_only"] and fixture["example"] and fixture["not_applied"]
    assert fixture["approved_final_translation"] is None


def test_no_automatic_approval_api_exists() -> None:
    assert not hasattr(governance, "auto_approve")


def test_boundary_is_fully_closed() -> None:
    boundary = json.loads(ARTIFACT.read_text(encoding="utf-8"))["boundary"]
    zero_fields = {"network_requests", "plans_applied", "approved_cases_created", "approved_translations_added", "existing_approved_translations_modified"}
    assert all(boundary[key] == 0 for key in zero_fields)
    assert all(value is False for key, value in boundary.items() if key not in zero_fields)


def test_builder_is_deterministic() -> None:
    assert _draft() == _draft()


def test_verify_corpus_integrity_accepts_matching_evidence() -> None:
    assert verify_corpus_integrity(_draft(), source_artifact=CORPUS, source_text=SOURCE_TEXT)


def test_validator_rejects_non_null_translation_before_approval() -> None:
    with pytest.raises(ValueError, match="null approved translation"):
        validate_governance_record(replace(_draft(), approved_final_translation="not approved"))
