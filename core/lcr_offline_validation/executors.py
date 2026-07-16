from __future__ import annotations

import hashlib
import json
from pathlib import Path

import core.character_memory_v2 as memory
import core.chunk_cache_v2 as cache
import core.context_scene_memory as context
import core.controlled_provider_routing as routing
import core.dual_pass_translation as dual_pass
import core.multilingual_profiles as multilingual
import core.post_polish_semantic_verification as semantic
from core.translation_intelligence_corpus.offline_quality_gate import evaluate_translation_candidate

from .models import ExecutorOutcome, ValidationScenario

T0="2026-07-16T00:00:00Z";T1="2026-07-16T00:01:00Z";T2="2026-07-16T00:02:00Z"
ROOT=Path(__file__).resolve().parents[2]


def _out(status,decision,*,issues=(),modules=None,evidence=(),outcomes=(),metrics=None,truth=None,executable=True):
    return ExecutorOutcome(status,decision,tuple(issues),dict(modules or {}),tuple(evidence),tuple(outcomes),dict(metrics or {}),truth,executable)


def _semantic_input(draft="他仍然記得這件事。",polish=None):
    polish=draft if polish is None else polish
    return semantic.create_verification_input(verification_id="batch9-verify",document_id="batch9-doc",chunk_index=0,source_language="ko",target_language="zh-Hant",source_text="고정 오프라인 근거",verified_draft_text=draft,polish_text=polish,polish_scope={"scope_type":"full_chunk"},character_memory_fingerprint=semantic.sha256_text("character"),context_scene_fingerprint=semantic.sha256_text("context"),glossary_fingerprint=semantic.sha256_text("glossary"),semantic_policy_id=semantic.POLICY_ID,semantic_policy_version=semantic.POLICY_VERSION,created_at=T0)


def _semantic_invariant(kind):
    return semantic.create_semantic_invariant(invariant_id="batch9-"+kind,invariant_type=kind,source_evidence="fixed synthetic source invariant",draft_evidence="fixed verified draft invariant",expected_value={"expected_value":"A","polish_value":"B"},approval_status="observed",origin="draft_verification")


def _cache_identity(index=0,**changes):
    values=dict(source_text=f"固定來源 {index}",prompt="prompt-v1",system_prompt="system-v1",policy={"quality":"v1"},context_selection={"selected":["ctx-1"]},glossary={"term":"value"},character_memory_selection_fingerprint=cache.sha256_text("char-selection"),context_scene_selection_fingerprint=cache.sha256_text("scene-selection"),language_profile_id="literary-ko-zh-hant",language_profile_version="1.0",source_language="ko",target_language="zh-Hant",provider_id="offline-provider-id",model_id="offline-model",provider_request_profile={"timeout":30},generation_settings={"temperature":0.2},quality_policy_id="quality-main",quality_policy_version="1",translation_engine_version="7.2",chunk_index=index,document_id="batch9-doc",chunking_strategy_id="paragraph",chunking_strategy_version="1",context_token_budget=512)
    values.update(changes);return cache.create_cache_identity(**values)


def _completed(store,index):
    entry=cache.create_cache_entry(_cache_identity(index),created_at=T0);cache.add_cache_entry(store,entry)
    return cache.complete_cache_entry(store,entry.cache_entry_id,translation_text=f"固定譯文 {index}",quality_status=cache.QualityStatus.PASSED,quality_evidence=({"gate":"pass"},),completed_at=T1)


def _routing_budget():
    return routing.ProviderRequestBudget(2,100,1,1,1,10000,5000,360)


def _timeout_budget(**changes):
    values=dict(per_attempt_timeout_seconds=180,maximum_chunk_wall_clock_seconds=360,maximum_document_timeout_events=3,provider_timeout_history=(),timeout_risk_level="low");values.update(changes);return routing.ProviderTimeoutBudget(**values)


def _routing_input(**changes):
    values=dict(document_id="batch9-doc",chunk_index=0,source_language="ko",target_language="zh-Hant",language_profile_id="literary-ko-zh-hant",language_profile_version="1.0",language_profile_fingerprint="1"*64,prompt_identity="prompt-v1",context_identity="context-v1",glossary_identity="glossary-v1",quality_policy_identity="literary-fidelity@1.0",semantic_policy_identity="semantic@1.0",semantic_verification_available=True,translation_mode="single_pass",draft_required=True,polish_required=False,estimated_input_tokens=1000,estimated_output_tokens=500,chunk_length=1000,provider_health_evidence={p.provider_id:"healthy" for p in routing.PROVIDER_PROFILES},provider_failure_history=(),cache_availability=False,verified_draft_available=False,request_budget=_routing_budget(),timeout_budget=_timeout_budget(),current_requests=0,current_document_requests=0,current_retry_requests=0,current_fallback_requests=0,current_polish_requests=0,current_input_tokens=0,current_output_tokens=0,current_wall_clock_seconds=0,manual_approval_granted=True,created_at=T0)
    values.update(changes);return routing.create_routing_input(**values)


def _failure(kind="read_timeout",count=1):
    return routing.ProviderFailureEvidence("batch9-"+kind,routing.NVIDIA_PROFILE.provider_id,routing.NVIDIA_PROFILE.model_id,kind,"prompt-v1",count,180 if "timeout" in kind else None,True,True,T0)


def _memory_evidence(kind,value,segment):
    return memory.create_evidence(evidence_type=kind,source_case_id="batch9",source_segment_id=segment,source_text_hash=hashlib.sha256((segment+value).encode()).hexdigest(),excerpt=value,language="ko",observed_at=T0)


def _memory_record(value,segment,*,approved=False):
    kind=memory.EvidenceType.HUMAN_APPROVED if approved else memory.EvidenceType.SOURCE_OBSERVATION
    kwargs={}
    if approved:kwargs={"approval_status":memory.ApprovalStatus.APPROVED,"approval_metadata":memory.ApprovalMetadata(value,T0,"reviewer","batch9-decision")}
    return memory.create_memory(character_id="char-1",fact_type=memory.FactType.CANONICAL_NAME,value=value,evidence=_memory_evidence(kind,value,segment),confidence=.9,created_at=T0,**kwargs)


def run_tic_quality_case(s:ValidationScenario)->ExecutorOutcome:
    fixture=json.loads((ROOT/"artifacts/tic_batch7/OFFLINE_QUALITY_GATE_FIXTURES.json").read_text(encoding="utf-8"))
    target=s.inputs["fixture_id"];item=next(x for x in fixture["items"] if x.get("fixture_id")==target)
    result=evaluate_translation_candidate(source_text=item["source_text"],translation_text=item["translation_text"],applicable_regression_ids=tuple(item["applicable_regression_ids"]),candidate_id=target)
    passed=result.gate_status=="pass";truth="approved" if item["kind"]=="human_approved" else "incorrect"
    metrics={"approved_cases_passed":int(truth=="approved" and passed),"historical_failures_rejected":int(item["kind"]=="historical_bad" and not passed)}
    return _out("passed" if passed else "failed","accept" if passed else "reject",issues=result.failure_reasons,modules={"offline_gate_status":result.gate_status,"regression_safe":result.regression_safe},evidence=(s.evidence_origin,target),metrics=metrics,truth=truth)


def run_golden_historical_case(s:ValidationScenario)->ExecutorOutcome:
    path=ROOT/s.inputs["artifact_path"]
    exists=path.is_file();digest=hashlib.sha256(path.read_bytes()).hexdigest() if exists else None
    return _out("insufficient_evidence","manual_review",issues=("historical_reference_has_no_executable_candidate_evidence",),modules={"artifact_exists":exists,"artifact_sha256":digest,"reference_only":True},evidence=(s.evidence_origin,str(path)),executable=False)


def run_memory_case(s:ValidationScenario)->ExecutorOutcome:
    kind=s.inputs["operation"]
    if kind=="approved_priority":
        store=memory.MemoryStore();record=_memory_record("鄭泰義","approved",approved=True);memory.add_or_merge_memory(store,record,now=T1);selected=memory.select_prompt_eligible_memories(store,character_ids=("char-1",),now=T2);ok=bool(selected.items) and selected.items[0].value=="鄭泰義"
        return _out("passed" if ok else "failed","accept" if ok else "blocked",modules={"selected_count":len(selected.items),"selected_value":selected.items[0].value if selected.items else None},evidence=(s.evidence_origin,record.memory_id))
    if kind=="conflict":
        store=memory.MemoryStore();memory.add_or_merge_memory(store,_memory_record("角色甲","a"),now=T1);result=memory.add_or_merge_memory(store,_memory_record("角色乙","b"),now=T2);conflict=result.disposition is memory.AddDisposition.CONFLICT
        return _out("conflict" if conflict else "passed","blocked" if conflict else "accept",modules={"disposition":result.disposition.value,"conflict_id":result.conflict.conflict_id if result.conflict else None},evidence=(s.evidence_origin,))
    store=cache.ChunkCacheStore();entry=_completed(store,0);changed=_cache_identity(0,character_memory_selection_fingerprint=cache.sha256_text("changed-selection"));lookup=cache.lookup_chunk_cache(store,changed,current_time=T2);stale=lookup.decision is cache.LookupDecision.STALE
    return _out("passed" if stale else "failed","reject" if stale else "accept",modules={"lookup_decision":lookup.decision.value,"reason":lookup.reason},outcomes=(() if stale else ("stale_cache_hit",)),evidence=(s.evidence_origin,entry.cache_entry_id))


def _context_record(value="主詞仍未解析",kind=context.ContextType.OTHER):
    ev=context.create_context_evidence(evidence_type=context.EvidenceType.SOURCE_OBSERVATION,source_case_id="batch9",source_segment_id="segment-1",source_text_hash=hashlib.sha256(value.encode()).hexdigest(),excerpt=value,language="ko",observed_at=T0)
    return context.create_context_memory(context_type=kind,value=value,evidence=ev,confidence=.95,scene_id="scene-1",chapter_id="chapter-1",sequence_index=1,approval_status=context.ApprovalStatus.PENDING,created_at=T0)


def run_context_scene_case(s:ValidationScenario)->ExecutorOutcome:
    operation=s.inputs["operation"]
    if operation in {"selection","unresolved_reference"}:
        store=context.ContextMemoryStore();record=_context_record(kind=context.ContextType.UNRESOLVED_REFERENCE if operation=="unresolved_reference" else context.ContextType.OTHER);context.add_or_merge_context(store,record,now=T1);selected=context.select_context_for_translation(store,chapter_id="chapter-1",scene_id="scene-1",sequence_index=1,now=T2);ok=any(x.item_id==record.context_id for x in selected.selected_records)
        return _out("passed" if ok else "failed","accept" if ok else "blocked",modules={"selected":ok,"context_type":record.context_type.value},outcomes=(() if ok else ("stale_context_selected",)),evidence=(s.evidence_origin,record.context_id))
    result=semantic.verify_post_polish_semantics(_semantic_input(),invariants=(_semantic_invariant("speaker"),));failed=result.status is semantic.VerificationStatus.FAILED
    return _out("failed" if failed else "passed","reject" if failed else "accept",issues=tuple(x.issue_type for x in result.issues),modules={"semantic_status":result.status.value},outcomes=(() if failed else ("pass",)),metrics={"blocking_mutations_detected":int(failed)},truth="incorrect",evidence=(s.evidence_origin,result.deterministic_fingerprint))


def run_cache_case(s:ValidationScenario)->ExecutorOutcome:
    if s.inputs["operation"]=="ten_chunk_plan":
        store=cache.ChunkCacheStore();identities=tuple(_cache_identity(i) for i in range(10));resume={}
        for i in range(8):
            entry=_completed(store,i);resume[i]={"document_id":"batch9-doc","chunk_index":i,"status":"completed","translation_hash":entry.translation_hash,"prompt_hash":entry.prompt_hash}
        timeout=cache.create_cache_entry(identities[8],created_at=T0);cache.add_cache_entry(store,timeout);cache.record_cache_failure(store,timeout.cache_entry_id,status="timeout",failure_type="temporary",attempt_count=1,failure_ttl=60,retry_after=T2,evidence=({"kind":"diagnostic"},),updated_at=T1)
        plan=cache.plan_chunk_reexecution(identities,store,resume_state=resume,current_time=T2);ok=plan.reusable_chunks==tuple(range(8)) and plan.retry_chunks==(8,9)
        return _out("passed" if ok else "failed","retry_required" if plan.retry_chunks else "use_cache",modules={"reusable":len(plan.reusable_chunks),"retry":len(plan.retry_chunks),"invalid":len(plan.invalid_chunks),"conflicts":len(plan.conflicts)},outcomes=(() if ok else ("partial_hit",)),metrics={"cache_reuse_count":len(plan.reusable_chunks),"retry_required_count":len(plan.retry_chunks)},evidence=(s.evidence_origin,))
    store=cache.ChunkCacheStore();entry=_completed(store,0);changed=_cache_identity(0,prompt="prompt-v2");lookup=cache.lookup_chunk_cache(store,changed,current_time=T2);safe=lookup.decision is cache.LookupDecision.STALE
    return _out("passed" if safe else "failed","reject" if safe else "accept",modules={"lookup_decision":lookup.decision.value,"reason":lookup.reason},outcomes=(() if safe else ("stale_cache_hit",)),evidence=(s.evidence_origin,entry.cache_entry_id))


def run_resume_case(s:ValidationScenario)->ExecutorOutcome:
    store=cache.ChunkCacheStore();entry=_completed(store,0)
    if s.inputs["operation"]=="resume_conflict":
        result=cache.reconcile_cache_with_resume(entry,{"document_id":"batch9-doc","chunk_index":0,"status":"completed","translation_hash":"0"*64,"prompt_hash":entry.prompt_hash});conflict=result.status is cache.ReconciliationStatus.CONFLICT
        return _out("conflict" if conflict else "passed","blocked" if conflict else "accept",issues=(result.reason,),modules={"reconciliation_status":result.status.value},outcomes=(() if conflict else ("silent_resume",)),evidence=(s.evidence_origin,entry.cache_entry_id))
    output=cache.build_cached_chunk_result(entry);check=cache.validate_cached_chunk_for_output((output,output),document_id="batch9-doc",expected_chunk_indexes=(0,1));blocked=not check["valid"]
    return _out("failed" if blocked else "passed","blocked" if blocked else "accept",issues=("duplicate_or_missing_or_partial",) if blocked else (),modules=check,outcomes=(() if blocked else ("assemble_partial",)),evidence=(s.evidence_origin,entry.cache_entry_id))


def _draft(status="verified",semantic_status="passed"):
    invariants={"subject_references":["A"],"pronoun_references":["A"],"named_entities":["A"],"numbers":["3"],"times":["today"],"negations":["not"],"causal_links":["a->b"],"relationships":["ally"],"speakers":["A"],"point_of_view":"third_person","locations":["room"],"events":["event"],"ambiguity_markers":["unknown"],"dialogue_boundaries":[1,2],"glossary_terms":{"term":"value"},"content_units":["u1","u2"]}
    return dual_pass.create_draft_result(draft_id="batch9-draft",document_id="batch9-doc",chunk_index=0,source_hash=dual_pass.sha("source"),prompt_identity=dual_pass.sha("prompt"),source_language="ko",target_language="zh-Hant",draft_text="他仍然記得這件事。",quality_status="passed",quality_evidence=({"gate":"pass"},),semantic_status=semantic_status,semantic_invariants=invariants,created_at=T0,status=status)


def _polish_trigger(draft):
    scope=dual_pass.create_polish_scope(scope_type="sentence_span",original_draft_hash=draft.draft_hash,selected_text="記得",surrounding_context=draft.draft_text,start_identifier="s1",end_identifier="s1",outside_before="他仍然",outside_after="這件事。")
    return dual_pass.create_polish_trigger(trigger_id="batch9-trigger",trigger_type="awkward_word_order",evidence=({"rule":"fixed"},),confidence=.9,severity="nonblocking",scope=scope,estimated_quality_value=.8,estimated_cost=20,eligible=True)


def run_dual_pass_case(s:ValidationScenario)->ExecutorOutcome:
    operation=s.inputs["operation"]
    if operation=="insufficient":return _out("insufficient_evidence","manual_review",issues=("fixed_executable_evidence_missing",),modules={"dual_pass_status":"not_executed"},evidence=(s.evidence_origin,),executable=False)
    draft=_draft(semantic_status="failed" if operation=="draft_failed" else "passed");triggers=() if operation=="no_trigger" else (_polish_trigger(draft),)
    decision=dual_pass.select_translation_mode(draft,triggers,provider_policy={"health":"provider_healthy","rollback_available":True},cost_policy={"allow_second_request":True},timeout_policy={"timeout_risk":.1},quality_policy={})
    if operation=="draft_failed":return _out("failed","blocked",modules={"mode":decision.mode.value,"estimated_requests":decision.estimated_requests},evidence=(s.evidence_origin,))
    if operation=="semantic_rollback":
        verified=semantic.verify_post_polish_semantics(_semantic_input(),invariants=(_semantic_invariant("subject_identity"),));view=semantic.build_batch5_verification_view(verified);recommendation=semantic.build_rollback_recommendation(verified,draft_identity="draft",polish_identity="polish");failed=verified.status is semantic.VerificationStatus.FAILED
        return _out("failed" if failed else "passed",recommendation["action"],issues=tuple(x.issue_type for x in verified.issues),modules={"batch5_mode":decision.mode.value,"batch6_view":view,"rollback":recommendation},metrics={"blocking_mutations_detected":int(failed)},truth="incorrect",evidence=(s.evidence_origin,verified.deterministic_fingerprint))
    expected_mode="single_pass" if operation=="no_trigger" else "selective_polish";ok=decision.mode.value==expected_mode
    return _out("passed" if ok else "failed","accept" if ok else "blocked",modules={"mode":decision.mode.value,"estimated_requests":decision.estimated_requests},evidence=(s.evidence_origin,))


SEMANTIC_KIND={"subject":"subject_identity","pronoun":"pronoun_reference","name_completion":"addition","number":"number","time":"time_expression","negation":"negation","causality":"causal_relation","omission":"omission","addition":"addition","ambiguity":"point_of_view","speaker":"speaker","scope":"action_agent"}
def run_semantic_case(s:ValidationScenario)->ExecutorOutcome:
    operation=s.inputs["operation"]
    if operation=="insufficient":return _out("insufficient_evidence","manual_review",issues=("fixed_executable_evidence_missing",),modules={"semantic_status":"not_executed"},evidence=(s.evidence_origin,),executable=False)
    if operation in {"punctuation_pass","numeric_equivalent"}:
        result=semantic.verify_post_polish_semantics(_semantic_input("他說。","他說！") if operation=="punctuation_pass" else _semantic_input("他等了三天。","他等了三天。"));passed=result.status is semantic.VerificationStatus.PASSED
        return _out("passed" if passed else "failed","accept" if passed else "rollback_to_draft",issues=tuple(x.issue_type for x in result.issues),modules={"semantic_status":result.status.value,"semantic_decision":result.decision.value},evidence=(s.evidence_origin,result.deterministic_fingerprint))
    structural_texts={
        "number":("\u4ed6\u7b49\u4e863\u5929\u3002","\u4ed6\u7b49\u4e864\u5929\u3002"),
        "time":("\u4ed6\u4eca\u5929\u62b5\u9054\u3002","\u4ed6\u660e\u5929\u62b5\u9054\u3002"),
        "negation":("\u4ed6\u6c92\u6709\u96e2\u958b\u3002","\u4ed6\u5df2\u7d93\u96e2\u958b\u3002"),
        "causality":("\u56e0\u70ba\u4e0b\u96e8\uff0c\u6240\u4ee5\u4ed6\u7559\u4e0b\u3002","\u96d6\u7136\u4e0b\u96e8\uff0c\u4f46\u662f\u4ed6\u96e2\u958b\u3002"),
    }
    if operation in structural_texts:
        draft,polish=structural_texts[operation];result=semantic.verify_post_polish_semantics(_semantic_input(draft,polish))
    else:result=semantic.verify_post_polish_semantics(_semantic_input(),invariants=(_semantic_invariant(SEMANTIC_KIND[operation]),))
    failed=result.status is semantic.VerificationStatus.FAILED
    return _out("failed" if failed else "passed",result.decision.value,issues=tuple(x.issue_type for x in result.issues),modules={"semantic_status":result.status.value,"semantic_decision":result.decision.value},outcomes=(() if failed else ("accept_polish",)),metrics={"blocking_mutations_detected":int(failed)},truth="incorrect",evidence=(s.evidence_origin,result.deterministic_fingerprint))


def run_multilingual_case(s:ValidationScenario)->ExecutorOutcome:
    selection=multilingual.select_language_profile(s.inputs["source_language"],s.inputs["target_language"],requested_profile_id=s.inputs.get("requested_profile_id"));selected=selection.status=="selected"
    return _out("passed" if selected else "invalid_input","accept" if selected else "blocked",modules={"selection_status":selection.status,"profile_id":selection.profile.profile_id if selection.profile else None},outcomes=(() if selected or selection.status!="selected" else ("profile_fallback",)),evidence=(s.evidence_origin,))


def run_provider_routing_case(s:ValidationScenario)->ExecutorOutcome:
    operation=s.inputs["operation"]
    if operation=="auth_no_retry":
        classification=routing.classify_provider_failure("authentication_failure");blocked=not classification["retryable"]
        return _out("failed" if blocked else "passed","blocked" if blocked else "accept",modules=classification,outcomes=(() if blocked else ("retry",)),evidence=(s.evidence_origin,))
    if operation=="repeated_timeout":
        failure=_failure(count=2);item=_routing_input(provider_failure_history=(failure,),current_retry_requests=1);retry=routing.evaluate_retry_eligibility(item,routing.NVIDIA_PROFILE,failure,attempts_for_provider=1);blocked=not retry.retry_allowed
        return _out("failed" if blocked else "passed","blocked" if blocked else "accept",modules={"retry_allowed":retry.retry_allowed,"reasons":retry.reasons},outcomes=(() if blocked else ("unbounded_retry",)),evidence=(s.evidence_origin,failure.evidence_id))
    if operation=="cross_provider_manual":
        failure=_failure();item=_routing_input(manual_approval_granted=False);fallback=routing.evaluate_fallback_eligibility(item,routing.NVIDIA_PROFILE,routing.GEMINI_PROFILE,failure);manual=fallback.status=="manual_approval_required"
        return _out("manual_review_required" if manual else "failed","manual_review" if manual else "blocked",modules={"fallback_status":fallback.status,"fallback_allowed":fallback.fallback_allowed},outcomes=(() if manual else ("automatic_fallback",)),evidence=(s.evidence_origin,failure.evidence_id))
    if operation=="budget_block":
        item=_routing_input(current_requests=2);decision=routing.select_provider_route(item,routing.PROVIDER_PROFILES);blocked=decision.decision=="blocked"
        return _out("failed" if blocked else "passed","blocked" if blocked else "accept",modules={"routing_decision":decision.decision,"reasons":decision.reasons},outcomes=(() if blocked else ("request_over_budget",)),evidence=(s.evidence_origin,decision.selected_provider or "blocked"))
    item=_routing_input();decision=routing.select_provider_route(item,routing.PROVIDER_PROFILES);plan=routing.build_provider_execution_plan(item,decision,routing.NVIDIA_PROFILE);safe=plan.prepare_only and not plan.executed and plan.network_requests==0
    return _out("passed" if safe else "failed","accept" if safe else "blocked",modules={"routing_decision":decision.decision,"prepare_only":plan.prepare_only,"executed":plan.executed,"network_requests":plan.network_requests},outcomes=(() if safe else ("provider_execution",)),metrics={"provider_requests_planned":decision.estimated_requests,"provider_requests_executed":int(plan.executed)},evidence=(s.evidence_origin,decision.selected_provider or "blocked"))


def run_cross_module_case(s:ValidationScenario)->ExecutorOutcome:
    profile=multilingual.select_language_profile("ko","zh-Hant");route_input=_routing_input(verified_draft_available=True,draft_required=False);route=routing.select_provider_route(route_input,routing.PROVIDER_PROFILES);plan=routing.build_provider_execution_plan(route_input,route,routing.NVIDIA_PROFILE)
    rollback=s.inputs["operation"]=="rollback";verified=semantic.verify_post_polish_semantics(_semantic_input(),invariants=(_semantic_invariant("subject_identity"),) if rollback else ());semantic_pass=verified.status is semantic.VerificationStatus.PASSED
    store=cache.ChunkCacheStore();entry=_completed(store,0);lookup=cache.lookup_chunk_cache(store,entry.identity,current_time=T2);cache_hit=lookup.decision is cache.LookupDecision.HIT
    safe=profile.status=="selected" and cache_hit and plan.prepare_only and not plan.executed
    if rollback:
        failed=verified.status is semantic.VerificationStatus.FAILED and safe
        return _out("failed" if failed else "passed","rollback_to_draft" if failed else "accept",issues=tuple(x.issue_type for x in verified.issues),modules={"profile":profile.profile.profile_id,"semantic":verified.status.value,"cache":lookup.decision.value,"routing":route.decision,"executed":plan.executed},outcomes=(() if failed else ("accept_polish",)),metrics={"blocking_mutations_detected":int(failed),"cache_reuse_count":int(cache_hit),"provider_requests_executed":int(plan.executed)},truth="incorrect",evidence=(s.evidence_origin,entry.cache_entry_id,verified.deterministic_fingerprint))
    passed=semantic_pass and safe
    return _out("passed" if passed else "failed","accept" if passed else "blocked",modules={"profile":profile.profile.profile_id,"semantic":verified.status.value,"cache":lookup.decision.value,"routing":route.decision,"executed":plan.executed},outcomes=(() if passed else ("semantic_change",)),metrics={"cache_reuse_count":int(cache_hit),"provider_requests_executed":int(plan.executed)},evidence=(s.evidence_origin,entry.cache_entry_id,verified.deterministic_fingerprint))


SCENARIO_EXECUTORS={
    "tic_quality_case":run_tic_quality_case,"memory_consistency_case":run_memory_case,
    "context_scene_case":run_context_scene_case,"cache_reuse_case":run_cache_case,
    "resume_reconciliation_case":run_resume_case,"dual_pass_case":run_dual_pass_case,
    "semantic_mutation_case":run_semantic_case,"multilingual_profile_case":run_multilingual_case,
    "provider_routing_case":run_provider_routing_case,"cross_module_case":run_cross_module_case,
    "golden_historical_case":run_golden_historical_case,
}
