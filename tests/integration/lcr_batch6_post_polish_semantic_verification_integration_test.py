from __future__ import annotations

import core.post_polish_semantic_verification as sv


def _item(text="他等了三天。", polish=None):
    return sv.create_verification_input(verification_id="integration", document_id="doc", chunk_index=1, source_language="ko", target_language="zh-Hant", source_text="source", verified_draft_text=text, polish_text=polish or text, polish_scope={"scope_type": "full_chunk"}, character_memory_fingerprint=sv.sha256_text("selected-character-view"), context_scene_fingerprint=sv.sha256_text("selected-scene-view"), glossary_fingerprint=sv.sha256_text("approved-glossary"), semantic_policy_id=sv.POLICY_ID, semantic_policy_version=sv.POLICY_VERSION, created_at="2026-07-16T00:00:00Z")


def test_batch5_interoperability_and_rollback_authority():
    passed = sv.verify_dual_pass_polish(_item())
    failed = sv.verify_dual_pass_polish(_item(polish="他等了四天。"))
    assert sv.build_batch5_verification_view(passed)["candidate_acceptable"]
    assert sv.build_batch5_verification_view(failed)["decision"] == "rollback_to_draft"


def test_selected_memory_context_glossary_and_policy_are_cache_identity_inputs():
    item = _item(); inv = sv.create_semantic_invariant(invariant_id="tic-subject", invariant_type="subject_identity", source_evidence="TIC fixed case", draft_evidence="approved subject correction", expected_value="far man", approval_status="human_approved", origin="tic_regression")
    result = sv.verify_post_polish_semantics(item, invariants=(inv,))
    identity = sv.build_verification_identity(item, invariant_fingerprint_value=sv.invariant_fingerprint((inv,)))
    assert result.status is sv.VerificationStatus.PASSED and len(identity) == 64


def test_tic_subject_shift_is_blocked_but_approved_lexical_choice_is_allowed():
    shift = sv.create_semantic_invariant(invariant_id="tic-shift", invariant_type="subject_identity", source_evidence="subject_reference_shift", draft_evidence="far man", expected_value={"expected_value": "far man", "polish_value": "Jeong"}, origin="tic_regression")
    lexical = sv.create_semantic_invariant(invariant_id="tic-lexical", invariant_type="glossary_term", source_evidence="lexical_choice", draft_evidence="approved human-person form", expected_value="人", approval_status="human_approved", origin="tic_regression")
    assert sv.verify_post_polish_semantics(_item(), invariants=(shift,)).status is sv.VerificationStatus.FAILED
    assert sv.verify_post_polish_semantics(_item(), invariants=(lexical,)).status is sv.VerificationStatus.PASSED


def test_offline_boundary_is_embedded_in_evidence():
    result = sv.verify_post_polish_semantics(_item())
    assert not result.evidence.provider_executed and result.evidence.network_requests == 0 and not result.evidence.new_translation_generated
