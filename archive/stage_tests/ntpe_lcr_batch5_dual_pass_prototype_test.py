from __future__ import annotations
import time
import core.dual_pass_translation as dp
T0="2026-07-16T00:00:00Z"
def invariants():return {"subject_references":["he=man"],"pronoun_references":["he=man"],"named_entities":["name"],"numbers":["3"],"times":["night"],"negations":["not"],"causal_links":[],"relationships":[],"speakers":[],"point_of_view":"third","locations":[],"events":["arrive"],"ambiguity_markers":["person"],"dialogue_boundaries":[],"glossary_terms":{},"content_units":["u1","u2"]}
def make_draft(i):return dp.create_draft_result(draft_id=f"draft-{i}",document_id="doc-root",chunk_index=i,source_hash=dp.sha(f"source-{i}"),prompt_identity=dp.sha("prompt"),source_language="ko",target_language="zh-TW",draft_text=f"verified draft {i}",quality_status="passed",semantic_status="passed",semantic_invariants=invariants(),created_at=T0,status="verified")
def make_scope(d):return dp.create_polish_scope(scope_type="sentence_span",original_draft_hash=d.draft_hash,selected_text=d.draft_text,surrounding_context=d.draft_text,start_identifier="s1",end_identifier="s1",outside_before="before",outside_after="after")
def make_candidate(d,i):return dp.create_polish_candidate(polish_id=f"polish-{i}",draft=d,polish_text=f"natural draft {i}",polish_scope=make_scope(d),polish_reason="word order",semantic_invariants=invariants(),created_at=T0,outside_before="before",outside_after="after")
def make_trigger(d,i):return dp.create_polish_trigger(trigger_id=f"trigger-{i}",trigger_type="awkward_word_order",evidence=({"fixture":i},),confidence=.9,severity="nonblocking",scope=make_scope(d),estimated_quality_value=.8,estimated_cost=10)
def timed(fn):start=time.perf_counter();value=fn();return value,(time.perf_counter()-start)*1000
def check(name,value):
    if not value:print("FAIL "+name);raise AssertionError(name)
    print("PASS "+name)
def main():
    drafts,draft_ms=timed(lambda:[make_draft(i) for i in range(100)]);check("100 Draft creation",len(drafts)==100 and draft_ms<50)
    candidates,polish_ms=timed(lambda:[make_candidate(d,i) for i,d in enumerate(drafts)]);check("100 Polish creation",len(candidates)==100 and polish_ms<50)
    triggers=[make_trigger(d,i) for i,d in enumerate(drafts)];evaluated,trigger_ms=timed(lambda:[dp.evaluate_polish_triggers((t,t)) for t in triggers]);check("100 trigger evaluation",all(len(x)==1 for x in evaluated) and trigger_ms<25)
    def decisions():return [dp.select_translation_mode(d,(t,),provider_policy={"health":"provider_healthy","rollback_available":True},cost_policy={"allow_second_request":True},timeout_policy={"timeout_risk":.1},quality_policy={}) for d,t in zip(drafts,triggers)]
    modes,mode_ms=timed(decisions);check("100 mode decisions",all(x.mode==dp.TranslationMode.SELECTIVE_POLISH for x in modes) and mode_ms<25)
    verifications,verify_ms=timed(lambda:[dp.verify_polish_candidate(f"source-{i}",d,p,semantic_policy={"version":"v1"}) for i,(d,p) in enumerate(zip(drafts,candidates))]);check("100 semantic verifications",all(x.status==dp.VerificationStatus.PASSED for x in verifications) and verify_ms<50)
    costs=[dp.estimate_provider_cost(mode=x.mode,draft_input_chars=100,draft_output_chars=100,polish_input_chars=50,polish_output_chars=50,provider_health="provider_healthy") for x in modes]
    plans,plan_ms=timed(lambda:[dp.build_dual_pass_execution_plan(m,triggers=(t,),cost_estimate=c,prepare_only=True) for m,t,c in zip(modes,triggers,costs)]);check("100 execution plans",all(not x.executed and x.prepare_only for x in plans) and plan_ms<25)
    def cache_ids():
        return [(dp.build_draft_cache_identity(source_hash=d.source_hash,prompt_identity=d.prompt_identity,draft_policy_version="d1",character_memory_selection_fingerprint=dp.sha("char"),context_scene_selection_fingerprint=dp.sha("scene"),glossary_fingerprint=dp.sha("glossary")),dp.build_polish_cache_identity(draft_hash=d.draft_hash,polish_policy_version="p1",polish_scope_hash=dp.sha("scope"),semantic_policy_version="s1",character_memory_selection_fingerprint=dp.sha("char"),context_scene_selection_fingerprint=dp.sha("scene"),glossary_fingerprint=dp.sha("glossary"))) for d in drafts]
    identities,cache_ms=timed(cache_ids);check("100 Draft Polish cache identities",len(identities)==100 and cache_ms<25)
    state={"mode":"selective_polish","verification_status":"passed","estimated_requests":2,"drafts":[{"draft_id":d.draft_id,"draft_hash":d.draft_hash} for d in drafts]};encoded,ser_ms=timed(lambda:dp.serialize_dual_pass_state(state));restored,deser_ms=timed(lambda:dp.deserialize_dual_pass_state(encoded));serialization_ms=ser_ms+deser_ms;check("serialization round trip",restored["mode"]=="selective_polish" and serialization_ms<75)
    decision=dp.decide_polish_rollback(drafts[0],candidates[0],verifications[0]);final,rollback_ms=timed(lambda:dp.apply_polish_rollback(drafts[0],candidates[0],decision));check("rollback decision application",final["final_hash"]==candidates[0].polish_hash and rollback_ms<10)
    evidence=dp.create_execution_evidence(plans[0]);check("offline execution boundary",not evidence.executed and not evidence.provider_executed and evidence.network_requests==0 and not evidence.new_translation_generated);check("schema",dp.SCHEMA_VERSION=="1.0")
    for name,value in (("draft_creation",draft_ms),("polish_creation",polish_ms),("trigger_evaluation",trigger_ms),("mode_decision",mode_ms),("semantic_verification",verify_ms),("execution_plan",plan_ms),("cache_identity",cache_ms),("serialization_round_trip",serialization_ms),("rollback",rollback_ms)):print(f"BENCHMARK {name}_ms={value:.3f}")
    print("ALL PASS")
if __name__=="__main__":main()
