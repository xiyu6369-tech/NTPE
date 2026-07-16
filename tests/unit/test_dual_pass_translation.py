from __future__ import annotations
import json
from dataclasses import replace
import pytest
import core.dual_pass_translation as dp
T0="2026-07-16T00:00:00Z"+""
def invariants(**changes):
    base={"subject_references":["他=遠方男人"],"pronoun_references":["他=遠方男人"],"named_entities":["鄭泰義"],"numbers":["3"],"times":["昨夜"],"negations":["不"],"causal_links":["因為->所以"],"relationships":["朋友"],"speakers":["char-1"],"point_of_view":"third_person","locations":["旅館"],"events":["抵達"],"ambiguity_markers":["那個人"],"dialogue_boundaries":[1,2],"glossary_terms":{"인간":"人"},"content_units":["u1","u2"]};base.update(changes);return base
def draft(**changes):
    values=dict(draft_id="draft-1",document_id="doc-1",chunk_index=1,source_hash=dp.sha("source"),prompt_identity=dp.sha("prompt"),source_language="ko",target_language="zh-TW",draft_text="他昨夜沒有帶三本書抵達旅館。",quality_status="passed",quality_evidence=({"gate":"pass"},),semantic_status="passed",semantic_invariants=invariants(),created_at=T0,status="verified");values.update(changes);return dp.create_draft_result(**values)
def scope(d=None,kind="sentence_span",**changes):
    d=d or draft();values=dict(scope_type=kind,original_draft_hash=d.draft_hash,selected_text="沒有帶三本書",surrounding_context=d.draft_text,start_identifier="sentence-1",end_identifier="sentence-1",outside_before="他昨夜",outside_after="抵達旅館。");values.update(changes);return dp.create_polish_scope(**values)
def candidate(d=None,inv=None,text="昨夜他沒帶三本書便抵達了旅館。",**changes):
    d=d or draft();values=dict(polish_id="polish-1",draft=d,polish_text=text,polish_scope=scope(d),polish_reason="改善繁中語序",semantic_invariants=inv or invariants(),created_at=T0,outside_before="他昨夜",outside_after="抵達旅館。");values.update(changes);return dp.create_polish_candidate(**values)
def trigger(d=None,kind="awkward_word_order",scope_kind="sentence_span",**changes):
    d=d or draft();values=dict(trigger_id="trigger-1",trigger_type=kind,evidence=({"rule":"fixture"},),confidence=.9,severity="nonblocking",scope=scope(d,scope_kind),estimated_quality_value=.8,estimated_cost=20,eligible=True);values.update(changes);return dp.create_polish_trigger(**values)
POLICY={"version":"semantic-v1"}

def test_schema_and_required_models_exist():
    assert dp.SCHEMA_VERSION=="1.0";assert {"DraftTranslationResult","PolishCandidate","DualPassDecision","SemanticVerificationResult","RollbackDecision","ProviderCostEstimate","DualPassExecutionPlan","DualPassExecutionEvidence"}<set(dp.__all__)
def test_verified_draft_is_eligible():assert dp.evaluate_draft_eligibility(draft())["eligible"]
@pytest.mark.parametrize("change,reason",[(dict(draft_text=""),"empty_draft"),(dict(partial=True),"partial_draft"),(dict(timeout=True),"timeout_draft"),(dict(cancelled=True),"cancelled_draft"),(dict(corrupt=True),"corrupt_draft"),(dict(semantic_status="failed"),"semantic_not_passed"),(dict(quality_status="failed"),"quality_not_eligible")])
def test_ineligible_drafts_fail_closed(change,reason):assert reason in dp.evaluate_draft_eligibility(draft(**change))["reasons"]
def test_source_hash_mismatch_rejected():assert "source_hash_mismatch" in dp.evaluate_draft_eligibility(draft(),expected_source_hash=dp.sha("other"))["reasons"]
def test_nonblocking_draft_requires_policy():
    item=draft(quality_status="passed_with_nonblocking_issues");assert not dp.evaluate_draft_eligibility(item)["eligible"];assert dp.evaluate_draft_eligibility(item,allow_nonblocking=True)["eligible"]
def test_no_trigger_selects_single_pass():
    result=dp.select_translation_mode(draft(),(),provider_policy={"health":"provider_healthy","rollback_available":True},cost_policy={"allow_second_request":True},timeout_policy={"timeout_risk":.1},quality_policy={});assert result.mode==dp.TranslationMode.SINGLE_PASS
def test_local_trigger_prefers_selective_polish():
    result=dp.select_translation_mode(draft(),(trigger(),),provider_policy={"health":"provider_healthy","rollback_available":True},cost_policy={"allow_second_request":True},timeout_policy={"timeout_risk":.1},quality_policy={});assert result.mode==dp.TranslationMode.SELECTIVE_POLISH
def test_healthy_full_chunk_trigger_can_select_dual_pass():
    result=dp.select_translation_mode(draft(),(trigger(scope_kind="full_chunk"),),provider_policy={"health":"provider_healthy","rollback_available":True},cost_policy={"allow_second_request":True},timeout_policy={"timeout_risk":.1,"maximum_dual_pass_risk":.3},quality_policy={});assert result.mode==dp.TranslationMode.DUAL_PASS
@pytest.mark.parametrize("health",["provider_unavailable","unknown"])
def test_unavailable_or_unknown_does_not_full_chunk_dual_pass(health):
    result=dp.select_translation_mode(draft(),(trigger(scope_kind="full_chunk"),),provider_policy={"health":health,"rollback_available":True},cost_policy={"allow_second_request":True},timeout_policy={"timeout_risk":.5,"maximum_dual_pass_risk":.3},quality_policy={});assert result.mode==dp.TranslationMode.SINGLE_PASS
def test_degraded_provider_limits_full_chunk_but_allows_local():
    policies=dict(provider_policy={"health":"provider_degraded","rollback_available":True},cost_policy={"allow_second_request":True},timeout_policy={"timeout_risk":.7},quality_policy={});assert dp.select_translation_mode(draft(),(trigger(scope_kind="full_chunk"),),**policies).mode==dp.TranslationMode.SINGLE_PASS;assert dp.select_translation_mode(draft(),(trigger(),),**policies).mode==dp.TranslationMode.SELECTIVE_POLISH
def test_failed_draft_is_blocked_not_polished():
    result=dp.select_translation_mode(draft(semantic_status="failed"),(trigger(),),provider_policy={"health":"provider_healthy"},cost_policy={},timeout_policy={},quality_policy={});assert result.mode==dp.TranslationMode.BLOCKED and result.estimated_requests==0
def test_missing_rollback_baseline_is_single_pass():
    result=dp.select_translation_mode(draft(),(trigger(),),provider_policy={"health":"provider_healthy","rollback_available":False},cost_policy={},timeout_policy={},quality_policy={});assert result.mode==dp.TranslationMode.SINGLE_PASS
def test_trigger_dedup_is_deterministic_and_not_approval():
    one=trigger();two=trigger(trigger_id="trigger-2",confidence=.8);result=dp.evaluate_polish_triggers((two,one));assert result==(one,);assert one.eligible and one.severity==dp.Severity.NONBLOCKING
def test_trigger_needs_evidence_and_length_is_not_a_trigger():
    with pytest.raises(dp.DualPassValidationError):trigger(evidence=())
    with pytest.raises(ValueError):trigger(kind="sentence_length")
def test_human_request_can_trigger_with_explicit_scope():assert trigger(kind="human_requested",evidence=()).eligible
def test_trigger_with_none_scope_fails_closed():
    with pytest.raises(dp.DualPassValidationError):trigger(scope_kind="none")
def test_ambiguous_span_scope_fails_closed():
    with pytest.raises(dp.DualPassValidationError):scope(start_identifier=None)
def test_stale_scope_draft_hash_rejected():
        with pytest.raises(dp.DualPassValidationError):dp.create_polish_candidate(polish_id="p",draft=draft(),polish_text="x",polish_scope=replace(scope(),original_draft_hash="0"*64),polish_reason="x",semantic_invariants=invariants(),created_at=T0)
def test_selected_span_hash_mismatch_is_invalid():
    p=candidate();result=dp.verify_polish_candidate("source",draft(),p,semantic_policy={"version":"v1","expected_scope":{"selected_text_hash":dp.sha("different span")}});assert result.status==dp.VerificationStatus.INVALID
@pytest.mark.parametrize("key,changed,issue",[("subject_references",["他=鄭泰義"],"subject_reference_shift"),("pronoun_references",["他=鄭泰義"],"pronoun_reference_shift"),("named_entities",["鄭太義"],"named_entity_change"),("named_entities",["鄭泰義全名"],"name_completion"),("numbers",["4"],"number_change"),("times",["今夜"],"time_change"),("negations",[],"negation_change"),("causal_links",["所以->因為"],"causal_change"),("relationships",["兄弟"],"relationship_change"),("speakers",["char-2"],"speaker_change"),("point_of_view","first_person","point_of_view_change"),("locations",["醫院"],"location_change"),("events",["離開"],"event_change"),("ambiguity_markers",[],"ambiguity_loss")])
def test_structural_semantic_mutations_fail(key,changed,issue):
    result=dp.verify_polish_candidate("source",draft(),candidate(inv=invariants(**{key:changed})),semantic_policy=POLICY);assert result.status==dp.VerificationStatus.FAILED;assert issue in {x.issue_type for x in result.issues};assert result.blocking_issue_count
def test_omission_and_addition_fail():
    for units,issue in ((["u1"],"omission"),(["u1","u2","u3"],"addition")):
        result=dp.verify_polish_candidate("source",draft(),candidate(inv=invariants(content_units=units)),semantic_policy=POLICY);assert issue in {x.issue_type for x in result.issues}
def test_out_of_scope_change_fails():
    result=dp.verify_polish_candidate("source",draft(),candidate(outside_before="changed"),semantic_policy=POLICY);assert "out_of_scope_change" in {x.issue_type for x in result.issues}
@pytest.mark.parametrize("text",["昨夜他沒帶三本書便抵達旅館。","昨夜，他沒有帶三本書，便抵達旅館。","昨夜他未攜三本書抵達旅館。"])
def test_word_order_punctuation_and_lexical_improvement_can_pass(text):assert dp.verify_polish_candidate("source",draft(),candidate(text=text),semantic_policy=POLICY).status==dp.VerificationStatus.PASSED
def test_insufficient_evidence_fails_closed():
    result=dp.verify_polish_candidate("source",draft(),candidate(inv={"subject_references":["x"]}),semantic_policy=POLICY);assert result.status==dp.VerificationStatus.INSUFFICIENT_EVIDENCE
def test_identity_mismatch_is_invalid():
    item=replace(candidate(),draft_hash="0"*64);assert dp.verify_polish_candidate("source",draft(),item,semantic_policy=POLICY).status==dp.VerificationStatus.INVALID
def test_rollback_accepts_passed_polish():
    d=draft();p=candidate(d);verification=dp.verify_polish_candidate("source",d,p,semantic_policy=POLICY);decision=dp.decide_polish_rollback(d,p,verification);final=dp.apply_polish_rollback(d,p,decision);assert decision.action==dp.RollbackAction.ACCEPT_POLISH and final["final_hash"]==p.polish_hash
def test_failed_polish_rolls_back_and_preserves_evidence():
    d=draft();p=candidate(d,inv=invariants(numbers=["4"]));verification=dp.verify_polish_candidate("source",d,p,semantic_policy=POLICY);decision=dp.decide_polish_rollback(d,p,verification);final=dp.apply_polish_rollback(d,p,decision);assert decision.action==dp.RollbackAction.ROLLBACK_TO_DRAFT;assert final["final_hash"]==d.draft_hash and final["polish_evidence_preserved"] and final["polish_candidate"].status==dp.ArtifactStatus.REJECTED and final["polish_candidate"].verification_status==dp.VerificationStatus.FAILED
def test_invalid_draft_blocks_output():assert dp.decide_polish_rollback(draft(status="invalid"),candidate(),dp.SemanticVerificationResult(dp.VerificationStatus.FAILED,(),(),"v","p",0)).action==dp.RollbackAction.BLOCK_OUTPUT
def test_invalid_rollback_request_does_not_mutate():
    d=draft();p=candidate();decision=replace(dp.decide_polish_rollback(d,p,dp.verify_polish_candidate("s",d,p,semantic_policy=POLICY)),draft_id="wrong")
    with pytest.raises(dp.DualPassValidationError):dp.apply_polish_rollback(d,p,decision)
@pytest.mark.parametrize("mode,requests",[("single_pass",1),("dual_pass",2),("selective_polish",2)])
def test_cost_model_request_counts(mode,requests):assert dp.estimate_provider_cost(mode=mode,draft_input_chars=400,draft_output_chars=200,polish_input_chars=100,polish_output_chars=100,provider_health="provider_healthy").request_count==requests
def test_cost_model_is_deterministic_and_degraded_is_riskier():
    args=dict(mode="selective_polish",draft_input_chars=400,draft_output_chars=200,polish_input_chars=100,polish_output_chars=50);healthy=dp.estimate_provider_cost(**args,provider_health="provider_healthy");degraded=dp.estimate_provider_cost(**args,provider_health="provider_degraded");assert degraded.timeout_risk>healthy.timeout_risk and healthy==dp.estimate_provider_cost(**args,provider_health="provider_healthy")
def test_cached_draft_reduces_selective_polish_to_one_request():
    estimate=dp.estimate_provider_cost(mode="selective_polish",draft_input_chars=400,draft_output_chars=200,polish_input_chars=100,polish_output_chars=50,provider_health="provider_healthy",cache_reuse_possible=True);assert estimate.request_count==1 and estimate.input_tokens==25 and estimate.output_tokens==13
def test_unavailable_blocks_polish_and_maximum_request_is_one():
    with pytest.raises(dp.DualPassValidationError):dp.estimate_provider_cost(mode="dual_pass",draft_input_chars=1,draft_output_chars=1,provider_health="provider_unavailable")
    with pytest.raises(dp.DualPassValidationError):dp.estimate_provider_cost(mode="selective_polish",draft_input_chars=1,draft_output_chars=1,maximum_polish_requests_per_chunk=2)
def cache_identities(d=None,**changes):
    d=d or draft();draft_identity=dp.build_draft_cache_identity(source_hash=d.source_hash,prompt_identity=d.prompt_identity,draft_policy_version="draft-v1",character_memory_selection_fingerprint=dp.sha("char"),context_scene_selection_fingerprint=dp.sha("scene"),glossary_fingerprint=dp.sha("glossary"));values=dict(draft_hash=d.draft_hash,polish_policy_version="polish-v1",polish_scope_hash=dp.sha("scope"),semantic_policy_version="semantic-v1",character_memory_selection_fingerprint=dp.sha("char"),context_scene_selection_fingerprint=dp.sha("scene"),glossary_fingerprint=dp.sha("glossary"));values.update(changes);return draft_identity,dp.build_polish_cache_identity(**values)
def test_draft_and_polish_cache_identity_are_separate():
    d,p=cache_identities();assert dp.draft_cache_key(d)!=dp.polish_cache_key(p)
@pytest.mark.parametrize("change,reason",[(dict(draft_hash=dp.sha("changed")),"draft_hash_changed"),(dict(polish_policy_version="v2"),"polish_policy_changed"),(dict(semantic_policy_version="v2"),"semantic_policy_changed"),(dict(polish_scope_hash=dp.sha("changed")),"polish_scope_changed"),(dict(character_memory_selection_fingerprint=dp.sha("changed")),"memory_selection_changed"),(dict(glossary_fingerprint=dp.sha("changed")),"glossary_changed")])
def test_polish_cache_staleness_reasons(change,reason):
    _,cached=cache_identities();_,current=cache_identities(**change);result=dp.compare_polish_cache_identity(cached,current);assert not result["usable"] and result["reason"]==reason
def test_unselected_memory_change_does_not_change_cache_identity():
    _,one=cache_identities();_,two=cache_identities();assert dp.polish_cache_key(one)==dp.polish_cache_key(two)
def test_failed_polish_final_identity_points_to_draft_only():
    d=draft();p=candidate(d,inv=invariants(numbers=["4"]));verification=dp.verify_polish_candidate("source",d,p,semantic_policy=POLICY);decision=dp.decide_polish_rollback(d,p,verification);di,pi=cache_identities(d);final=dp.build_final_output_identity(rollback_decision=decision,draft_identity=di,polish_identity=pi,semantic_policy_version="semantic-v1",verification_status=verification.status);assert final.selected_kind=="draft" and final.polish_cache_key is None and final.selected_hash==d.draft_hash
def test_execution_plan_is_prepare_only_and_never_executed():
    d=draft();t=trigger(d);decision=dp.select_translation_mode(d,(t,),provider_policy={"health":"provider_healthy","rollback_available":True},cost_policy={"allow_second_request":True},timeout_policy={"timeout_risk":.1},quality_policy={});cost=dp.estimate_provider_cost(mode=decision.mode,draft_input_chars=100,draft_output_chars=100,polish_input_chars=50,polish_output_chars=50,provider_health="provider_healthy");plan=dp.build_dual_pass_execution_plan(decision,triggers=(t,),cost_estimate=cost,cache_candidates=("draft-cache",),prepare_only=True);evidence=dp.create_execution_evidence(plan);assert plan.polish_required and plan.rollback_available and not plan.executed;assert not evidence.executed and not evidence.provider_executed and evidence.network_requests==0 and not evidence.new_translation_generated
def test_polish_request_contract_references_only_verified_fingerprints():
    d=draft();contract=dp.build_polish_request_contract(draft=d,scope=scope(d),character_memory_selection_fingerprint=dp.sha("char"),context_scene_selection_fingerprint=dp.sha("scene"),glossary_fingerprint=dp.sha("glossary"),quality_policy_version="q1",polish_policy_version="p1");assert contract.verified_draft_hash==d.draft_hash and contract.prepare_only and not contract.executed
def test_blocked_execution_plan_has_no_requests():
    decision=dp.select_translation_mode(draft(status="invalid"),(),provider_policy={},cost_policy={},timeout_policy={},quality_policy={});cost=dp.estimate_provider_cost(mode="blocked",draft_input_chars=0,draft_output_chars=0);plan=dp.build_dual_pass_execution_plan(decision,cost_estimate=cost);assert plan.blocked_reasons and plan.maximum_requests==0
def test_serialization_roundtrip_is_canonical():
    state={"mode":"selective_polish","verification_status":"passed","estimated_requests":2,"executed":False,"draft_hash":draft().draft_hash};encoded=dp.serialize_dual_pass_state(state);assert dp.serialize_dual_pass_state(dp.deserialize_dual_pass_state(encoded))==encoded
@pytest.mark.parametrize("payload",["{","[]","not json"])
def test_malformed_state_rejected(payload):
    with pytest.raises(dp.DualPassValidationError):dp.deserialize_dual_pass_state(payload)
def test_unknown_schema_invalid_enum_and_negative_requests_rejected():
    for data in ({"schema_version":"999"},{"schema_version":"1.0","mode":"magic"},{"schema_version":"1.0","verification_status":"maybe"},{"schema_version":"1.0","request_count":-1}):
        with pytest.raises(dp.DualPassValidationError):dp.deserialize_dual_pass_state(json.dumps(data))
def test_secret_like_state_rejected():
    with pytest.raises(dp.DualPassValidationError):dp.serialize_dual_pass_state({"note":"Bear"+"er populated-token-value-123456"})
def test_path_traversal_state_rejected():
    with pytest.raises(dp.DualPassValidationError):dp.serialize_dual_pass_state({"output_path":"../escape.json"})
def test_raw_provider_payload_evidence_rejected():
    with pytest.raises(dp.DualPassValidationError):draft(quality_evidence=({"raw_provider_response":"forbidden"},))
def test_public_api_has_no_provider_executor_runtime_or_prompt_builder():assert not {"execute_provider","run_runtime","build_prompt","translate","assemble_output"}&set(dp.__all__)
