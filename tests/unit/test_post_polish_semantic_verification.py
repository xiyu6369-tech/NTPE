from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest
import core.post_polish_semantic_verification as sv

T0 = "2026-07-16T00:00:00Z"


def make_input(draft="他昨天等了三天，因為下雨，所以沒有離開。", polish=None, scope=None, **changes):
    polish = draft if polish is None else polish
    values = dict(verification_id="verify-1", document_id="doc-1", chunk_index=0, source_language="ko", target_language="zh-Hant", source_text="source fixture", verified_draft_text=draft, polish_text=polish, polish_scope=scope or {"scope_type": "full_chunk"}, character_memory_fingerprint=sv.sha256_text("selected-character-memory"), context_scene_fingerprint=sv.sha256_text("selected-context"), glossary_fingerprint=sv.sha256_text("glossary"), semantic_policy_id=sv.POLICY_ID, semantic_policy_version=sv.POLICY_VERSION, created_at=T0)
    values.update(changes)
    return sv.create_verification_input(**values)


def invariant(kind, expected=None, **changes):
    values = dict(invariant_id="inv-" + kind, invariant_type=kind, source_evidence="provided source invariant", draft_evidence="verified draft invariant", expected_value=expected, approval_status="observed", origin="draft_verification")
    values.update(changes)
    return sv.create_semantic_invariant(**values)


@pytest.mark.parametrize("field,text", [("source_hash", "bad source"), ("verified_draft_hash", "bad draft"), ("polish_hash", "bad polish")])
def test_hash_mismatch_is_invalid(field, text):
    item = replace(make_input(), **{field: sv.sha256_text(text)})
    result = sv.verify_post_polish_semantics(item)
    assert result.status is sv.VerificationStatus.INVALID_INPUT and result.decision is sv.VerificationDecision.BLOCK_OUTPUT


@pytest.mark.parametrize("field", ["source_text", "verified_draft_text", "polish_text"])
def test_empty_input_is_invalid(field):
    item = make_input(**{field: ""})
    assert sv.verify_post_polish_semantics(item).status is sv.VerificationStatus.INVALID_INPUT


def test_unknown_policy_is_invalid():
    assert sv.verify_post_polish_semantics(replace(make_input(), semantic_policy_version="9.9")).status is sv.VerificationStatus.INVALID_INPUT


def test_conflicting_approved_evidence_is_conflict():
    inv = invariant("subject_identity", "A", approval_status="conflicting", origin="human_approved")
    result = sv.verify_post_polish_semantics(make_input(), invariants=(inv,))
    assert result.status is sv.VerificationStatus.CONFLICT and result.decision is sv.VerificationDecision.BLOCK_OUTPUT


@pytest.mark.parametrize("draft,polish,kind", [("他等了三天。", "他等了四天。", "number"), ("他昨天抵達。", "他前天抵達。", "time_expression"), ("他不可能離開。", "他可能離開。", "negation"), ("或許他會來。", "他一定會來。", "modality"), ("因為下雨，所以他留下。", "雖然下雨，但是他留下。", "causal_relation")])
def test_structural_changes_fail(draft, polish, kind):
    result = sv.verify_post_polish_semantics(make_input(draft, polish))
    assert result.status is sv.VerificationStatus.FAILED and kind in {x.issue_type for x in result.issues}
    assert result.decision is sv.VerificationDecision.ROLLBACK_TO_DRAFT


def test_numeric_format_same_value_passes():
    assert sv.verify_post_polish_semantics(make_input("他等了3天。", "他等了三天。" )).status is sv.VerificationStatus.PASSED


def test_punctuation_only_change_passes():
    assert sv.verify_post_polish_semantics(make_input("他回來了。", "他回來了！")).status is sv.VerificationStatus.PASSED


def test_name_completion_fails():
    result = sv.verify_post_polish_semantics(make_input("李安。", "李安國。"))
    assert result.status is sv.VerificationStatus.FAILED and "name_completion" in {x.issue_type for x in result.issues}


@pytest.mark.parametrize("kind", ["subject_identity", "pronoun_reference", "speaker", "action_agent", "action_patient", "event_presence", "relationship", "point_of_view", "omission", "addition"])
def test_provided_invariant_change_fails(kind):
    inv = invariant(kind, {"expected_value": "A", "polish_value": "B"})
    result = sv.verify_post_polish_semantics(make_input(), invariants=(inv,))
    assert result.status is sv.VerificationStatus.FAILED and kind in {x.issue_type for x in result.issues}


def test_unresolved_reference_forced_resolution_fails():
    inv = invariant("pronoun_reference", {"expected_value": "unresolved", "polish_value": "A"}, approval_status="unresolved")
    assert sv.verify_post_polish_semantics(make_input(), invariants=(inv,)).status is sv.VerificationStatus.FAILED


def test_human_approved_resolution_and_name_variant_pass():
    inv = invariant("pronoun_reference", "A", approval_status="human_approved", origin="human_approved")
    assert sv.verify_post_polish_semantics(make_input(), invariants=(inv,)).status is sv.VerificationStatus.PASSED


def test_ambiguity_loss_fails():
    result = sv.verify_post_polish_semantics(make_input("那個人可能幾天後來。", "王明三天後一定會來。"))
    assert result.status is sv.VerificationStatus.FAILED and "ambiguity_loss" in {x.issue_type for x in result.issues}


def test_selective_scope_outside_change_is_invalid():
    scope = {"scope_type": "sentence_span", "draft_before": "甲。", "draft_selected": "舊。", "draft_after": "乙。", "polish_before": "丙。", "polish_selected": "新。", "polish_after": "乙。"}
    result = sv.verify_post_polish_semantics(make_input("甲。舊。乙。", "丙。新。乙。", scope))
    assert result.status is sv.VerificationStatus.INVALID_INPUT


def test_valid_selective_scope_continues_verification():
    scope = {"scope_type": "sentence_span", "draft_before": "甲。", "draft_selected": "舊。", "draft_after": "乙。", "polish_before": "甲。", "polish_selected": "新。", "polish_after": "乙。"}
    assert sv.verify_post_polish_semantics(make_input("甲。舊。乙。", "甲。新。乙。", scope)).status is sv.VerificationStatus.PASSED


def test_serialization_is_deterministic_round_trip():
    result = sv.verify_post_polish_semantics(make_input())
    encoded = sv.serialize_verification_result(result)
    decoded = sv.deserialize_verification_result(encoded)
    sv.validate_verification_result(decoded)
    assert sv.serialize_verification_result(decoded) == encoded


@pytest.mark.parametrize("payload", ["{", "[]", '{"schema_version":"9.9"}', '{"schema_version":"1.0","status":"magic"}', '{"schema_version":"1.0","output_path":"../escape"}'])
def test_bad_serialization_rejected(payload):
    with pytest.raises(ValueError): sv.deserialize_verification_result(payload)


def test_identity_changes_only_for_selected_inputs():
    item = make_input(); fp = sv.invariant_fingerprint(())
    one = sv.build_verification_identity(item, invariant_fingerprint_value=fp)
    assert one == sv.build_verification_identity(item, invariant_fingerprint_value=fp)
    assert one != sv.build_verification_identity(replace(item, semantic_policy_version="1.1"), invariant_fingerprint_value=fp)
    assert one != sv.build_verification_identity(replace(item, polish_text="改", polish_hash=sv.sha256_text("改")), invariant_fingerprint_value=fp)
    assert one != sv.build_verification_identity(replace(item, character_memory_fingerprint=sv.sha256_text("changed selected")), invariant_fingerprint_value=fp)


def test_batch5_view_and_rollback_mapping():
    passed = sv.verify_post_polish_semantics(make_input())
    failed = sv.verify_post_polish_semantics(make_input("三天", "四天"))
    assert sv.build_batch5_verification_view(passed)["decision"] == "accept_polish"
    recommendation = sv.build_rollback_recommendation(failed, draft_identity="draft", polish_identity="polish")
    assert recommendation["action"] == "rollback_to_draft" and recommendation["selected_identity"] == "draft" and not recommendation["final_polish_cache_eligible"]


def test_insufficient_evidence_never_accepts_polish():
    policy = replace(sv.DEFAULT_POLICY, minimum_evidence=100)
    result = sv.verify_post_polish_semantics(make_input(), policy=policy)
    assert result.status is sv.VerificationStatus.INSUFFICIENT_EVIDENCE
    assert result.decision is sv.VerificationDecision.MANUAL_REVIEW_REQUIRED
    assert not sv.build_batch5_verification_view(result)["candidate_acceptable"]


def test_invalid_input_maps_to_block_output():
    result = sv.verify_post_polish_semantics(replace(make_input(), source_hash="0" * 64))
    assert sv.build_batch5_verification_view(result)["decision"] == "block_output"


def test_public_api_has_no_executor_provider_prompt_or_runtime():
    assert not {"translate", "execute_provider", "build_prompt", "assemble_output", "run_runtime"} & set(sv.__all__)


def test_fixture_is_synthetic_not_tic_approved():
    payload = json.loads((Path(__file__).parents[1] / "fixtures/lcr_batch6/semantic_regressions.json").read_text(encoding="utf-8"))
    assert payload["fixture_kind"] == "LCR Batch 6 synthetic structural fixture" and payload["tic_human_approved_evidence"] is False and len(payload["items"]) == 10
