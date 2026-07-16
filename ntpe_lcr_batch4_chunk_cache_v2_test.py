from __future__ import annotations
import time
import core.chunk_cache_v2 as cc
T0="2026-07-16T00:00:00Z";T1="2026-07-16T00:01:00Z";T2="2026-07-16T00:02:00Z"
def identity(index):return cc.create_cache_identity(source_text=f"source {index}",prompt="prompt",system_prompt="system",policy={"v":1},context_selection=["ctx"],glossary={"v":1},character_memory_selection_fingerprint=cc.sha256_text("char"),context_scene_selection_fingerprint=cc.sha256_text("scene"),language_profile_id="profile",language_profile_version="1",source_language="ko",target_language="zh-TW",provider_id="offline-id",model_id="model",provider_request_profile={"timeout":30},generation_settings={"temperature":0},quality_policy_id="quality",quality_policy_version="1",translation_engine_version="7.2",chunk_index=index,document_id="doc-root",chunking_strategy_id="paragraph",chunking_strategy_version="1",context_token_budget=512)
def timed(fn):start=time.perf_counter();value=fn();return value,(time.perf_counter()-start)*1000
def check(name,value):
    if not value:print("FAIL "+name);raise AssertionError(name)
    print("PASS "+name)
def main():
    identities,identity_ms=timed(lambda:[identity(i) for i in range(100)]);check("100 identity generation",len({cc.cache_key_for_identity(x) for x in identities})==100 and identity_ms<50)
    store=cc.ChunkCacheStore()
    def add_all():
        entries=[]
        for item in identities:
            entry=cc.create_cache_entry(item,created_at=T0);cc.add_cache_entry(store,entry);entries.append(cc.complete_cache_entry(store,entry.cache_entry_id,translation_text=f"translation {item.chunk_index}",quality_status="passed",quality_evidence=({"gate":"pass"},),completed_at=T1))
        return entries
    entries,add_ms=timed(add_all);check("100 completed add",len(store.entries)==100 and add_ms<100)
    results,lookup_ms=timed(lambda:[cc.lookup_chunk_cache(store,item,current_time=T2) for item in identities]);print(f"BENCHMARK lookup_ms={lookup_ms:.3f}");check("100 lookup",all(x.decision==cc.LookupDecision.HIT for x in results) and lookup_ms<25)
    resumes=[{"chunk_index":e.chunk_index,"document_id":e.document_id,"status":"DONE","translation_hash":e.translation_hash,"prompt_hash":e.prompt_hash} for e in entries]
    reconciled,reconcile_ms=timed(lambda:[cc.reconcile_cache_with_resume(store.get(e.cache_entry_id),r) for e,r in zip(entries,resumes)]);check("100 resume reconciliation",all(x.status==cc.ReconciliationStatus.CONSISTENT for x in reconciled) and reconcile_ms<25)
    retry_plan,retry_ms=timed(lambda:cc.plan_chunk_reexecution(identities,store,{x["chunk_index"]:x for x in resumes},current_time=T2));check("100 chunk retry planning",len(retry_plan.reusable_chunks)==100 and retry_ms<25)
    encoded,serialize_ms=timed(lambda:cc.serialize_cache_store(store));restored,deserialize_ms=timed(lambda:cc.deserialize_cache_store(encoded));serialization_ms=serialize_ms+deserialize_ms;check("serialization round trip",restored.to_dict()==store.to_dict() and serialization_ms<75)
    retention,retention_ms=timed(lambda:cc.plan_cache_retention(store,policy=cc.RetentionPolicy(maximum_entries=90),current_time=T2));check("retention planning",len(retention.remove_entry_ids)==10 and retention_ms<25)
    first=entries[0];cc.invalidate_cache_entry(store,first.cache_entry_id,reason="manual",invalidated_at="2026-07-16T00:03:00Z");rolled,rollback_ms=timed(lambda:cc.rollback_cache_entry(store,first.cache_entry_id,target_version=2,current_identity=first.identity,rolled_back_at="2026-07-16T00:04:00Z"));check("rollback",rolled.status==cc.CacheStatus.COMPLETED and rollback_ms<10)
    check("completed eligibility",all(x.validation_passed and not x.partial and not x.timeout for x in entries));check("production boundary",not {"translate","run_runtime","execute_provider","assemble_output"}&set(cc.__all__));check("schema",cc.SCHEMA_VERSION=="2.0")
    for name,value in (("identity_generation",identity_ms),("add_completed",add_ms),("resume_reconciliation",reconcile_ms),("retry_planning",retry_ms),("serialization_round_trip",serialization_ms),("retention_planning",retention_ms),("rollback",rollback_ms)):print(f"BENCHMARK {name}_ms={value:.3f}")
    print("ALL PASS")
if __name__=="__main__":main()
