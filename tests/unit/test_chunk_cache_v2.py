from __future__ import annotations
import json
from dataclasses import replace
from pathlib import Path
import pytest
import core.chunk_cache_v2 as cc

T0="2026-07-16T00:00:00Z";T1="2026-07-16T00:01:00Z";T2="2026-07-16T00:02:00Z"


def identity(index=1,**changes):
    values=dict(source_text=f"原文 {index}\n保留標點。",prompt="prompt-v1",system_prompt="system-v1",policy={"quality":"v1"},context_selection={"selected":["ctx-1"]},glossary={"版本":"v1"},character_memory_selection_fingerprint=cc.sha256_text("char-selection"),context_scene_selection_fingerprint=cc.sha256_text("scene-selection"),language_profile_id="literary-zh-tw",language_profile_version="1",source_language="ko",target_language="zh-TW",provider_id="offline-provider-id",model_id="model-v1",provider_request_profile={"timeout":30},generation_settings={"temperature":0.2},quality_policy_id="quality-main",quality_policy_version="1",translation_engine_version="7.2",chunk_index=index,document_id="doc-1",chunking_strategy_id="paragraph",chunking_strategy_version="1",context_token_budget=512)
    values.update(changes);return cc.create_cache_identity(**values)


def completed(store=None,index=1,text=None,quality=cc.QualityStatus.PASSED,**identity_changes):
    store=store or cc.ChunkCacheStore();entry=cc.create_cache_entry(identity(index,**identity_changes),created_at=T0);cc.add_cache_entry(store,entry);entry=cc.complete_cache_entry(store,entry.cache_entry_id,translation_text=text or f"譯文 {index}",quality_status=quality,quality_evidence=({"gate":"pass"},),completed_at=T1);return store,entry


def test_schema_and_identity_contains_required_fingerprints():
    item=identity();assert cc.SCHEMA_VERSION=="2.0";assert item.character_memory_selection_fingerprint;assert item.context_scene_selection_fingerprint;assert item.context_token_budget==512


def test_canonical_key_is_deterministic_and_dictionary_order_independent():
    one=identity(policy={"a":1,"b":2},generation_settings={"x":1,"y":2});two=identity(policy={"b":2,"a":1},generation_settings={"y":2,"x":1});assert cc.cache_key_for_identity(one)==cc.cache_key_for_identity(two)


@pytest.mark.parametrize("field,change",[("source_text","不同原文"),("prompt","prompt-v2"),("system_prompt","system-v2"),("context_selection",{"selected":["ctx-2"]}),("glossary",{"版本":"v2"}),("provider_id","other-provider"),("model_id","model-v2"),("generation_settings",{"temperature":0.3}),("language_profile_version","2"),("quality_policy_version","2"),("translation_engine_version","7.3"),("context_token_budget",256)])
def test_all_semantic_identity_changes_change_key(field,change):
    assert cc.cache_key_for_identity(identity())!=cc.cache_key_for_identity(identity(**{field:change}))


def test_source_normalization_preserves_newlines_and_punctuation():
    assert cc.normalize_source("A。\r\nB！")=="A。\nB！"


def test_absolute_path_and_credential_identity_fail_closed():
    with pytest.raises(cc.ChunkCacheValidationError):cc.create_cache_entry(identity(document_id="C:\\secret\\book.txt"),created_at=T0)
    with pytest.raises(cc.ChunkCacheValidationError):cc.create_cache_entry(identity(provider_id="Bear"+"er token-value-123456"),created_at=T0)


def test_valid_completed_entry_hits_and_updates_access_metadata():
    store,entry=completed();result=cc.lookup_chunk_cache(store,entry.identity,current_time=T2);assert result.decision==cc.LookupDecision.HIT;assert result.entry.hit_count==1;assert result.validation_results["quality"]


def test_empty_or_unacceptable_completed_entry_rejected():
    store=cc.ChunkCacheStore();entry=cc.create_cache_entry(identity(),created_at=T0);cc.add_cache_entry(store,entry)
    with pytest.raises(cc.ChunkCacheValidationError):cc.complete_cache_entry(store,entry.cache_entry_id,translation_text="",quality_status="passed",completed_at=T1)
    with pytest.raises(cc.ChunkCacheValidationError):cc.complete_cache_entry(store,entry.cache_entry_id,translation_text="譯文",quality_status="failed",completed_at=T1)


def test_nonblocking_quality_requires_explicit_policy():
    store,entry=completed(quality=cc.QualityStatus.PASSED_WITH_NONBLOCKING_ISSUES);assert cc.lookup_chunk_cache(store,entry.identity,current_time=T2).decision==cc.LookupDecision.INELIGIBLE;assert cc.lookup_chunk_cache(store,entry.identity,cache_policy=cc.CachePolicy(True),current_time=T2).decision==cc.LookupDecision.HIT


@pytest.mark.parametrize("status,reason",[("partial","partial_entry"),("failed","failed_entry"),("timeout","timeout_entry")])
def test_failure_entries_are_retry_required_and_preserve_evidence(status,reason):
    store=cc.ChunkCacheStore();entry=cc.create_cache_entry(identity(),created_at=T0);cc.add_cache_entry(store,entry);failed=cc.record_cache_failure(store,entry.cache_entry_id,status=status,failure_type="temporary",attempt_count=2,failure_ttl=60,retry_after=T2,evidence=({"kind":"diagnostic"},),updated_at=T1,partial_text="不完整" if status=="partial" else None);result=cc.lookup_chunk_cache(store,failed.identity,current_time=T2);assert result.decision==cc.LookupDecision.RETRY_REQUIRED and result.reason==reason;assert failed.quality_evidence


def test_cancelled_stale_and_prepared_never_hit():
    for status in ("cancelled",):
        store=cc.ChunkCacheStore();entry=cc.create_cache_entry(identity(),created_at=T0);cc.add_cache_entry(store,entry);failed=cc.record_cache_failure(store,entry.cache_entry_id,status=status,failure_type="cancel",attempt_count=1,failure_ttl=60,updated_at=T1);assert cc.lookup_chunk_cache(store,failed.identity,current_time=T2).decision==cc.LookupDecision.INVALID
    store,entry=completed();cc.invalidate_cache_entry(store,entry.cache_entry_id,reason="manual_invalidation",invalidated_at=T2);assert cc.lookup_chunk_cache(store,entry.identity,current_time=T2).decision==cc.LookupDecision.STALE
    store=cc.ChunkCacheStore();entry=cc.create_cache_entry(identity(),created_at=T0);cc.add_cache_entry(store,entry);assert cc.lookup_chunk_cache(store,entry.identity,current_time=T1).decision==cc.LookupDecision.INELIGIBLE


@pytest.mark.parametrize("change,reason",[(dict(source_text="changed"),"source_changed"),(dict(prompt="changed"),"prompt_changed"),(dict(context_selection={"selected":[]}),"context_changed"),(dict(glossary={}),"glossary_changed"),(dict(provider_id="provider-2"),"provider_changed"),(dict(model_id="model-2"),"model_changed"),(dict(quality_policy_version="2"),"quality_policy_changed")])
def test_lookup_explains_identity_change(change,reason):
    store,entry=completed();result=cc.lookup_chunk_cache(store,identity(**change),current_time=T2);assert result.decision==cc.LookupDecision.STALE and result.reason==reason


def test_translation_hash_corruption_is_invalid_not_hit():
    store,entry=completed();store.entries[entry.cache_entry_id]=replace(entry,translation_hash="0"*64);result=cc.lookup_chunk_cache(store,entry.identity,current_time=T2);assert result.decision==cc.LookupDecision.INVALID


def test_manual_invalidation_preserves_translation_and_reason():
    store,entry=completed();stale=cc.invalidate_cache_entry(store,entry.cache_entry_id,reason="human_correction",invalidated_at=T2);assert stale.translation_text==entry.translation_text;assert stale.invalidated_reason=="human_correction";assert store.history[entry.cache_entry_id]


def test_rollback_completed_version_requires_current_identity():
    store,entry=completed();cc.invalidate_cache_entry(store,entry.cache_entry_id,reason="manual",invalidated_at=T2);rolled=cc.rollback_cache_entry(store,entry.cache_entry_id,target_version=2,current_identity=entry.identity,rolled_back_at="2026-07-16T00:03:00Z");assert rolled.status==cc.CacheStatus.COMPLETED;assert cc.lookup_chunk_cache(store,entry.identity,current_time="2026-07-16T00:04:00Z").decision==cc.LookupDecision.HIT


def test_stale_identity_rollback_does_not_become_hit_and_invalid_target_is_atomic():
    store,entry=completed();cc.invalidate_cache_entry(store,entry.cache_entry_id,reason="manual",invalidated_at=T2);rolled=cc.rollback_cache_entry(store,entry.cache_entry_id,target_version=2,current_identity=identity(prompt="new"),rolled_back_at="2026-07-16T00:03:00Z");assert rolled.status==cc.CacheStatus.ROLLED_BACK
    before=cc.serialize_cache_store(store)
    with pytest.raises(cc.ChunkCacheValidationError):cc.rollback_cache_entry(store,entry.cache_entry_id,target_version=99)
    assert cc.serialize_cache_store(store)==before


def test_snapshot_restore_and_serialization_are_deterministic():
    store,entry=completed();encoded=cc.serialize_cache_store(store);restored=cc.deserialize_cache_store(encoded);assert cc.serialize_cache_store(restored)==encoded;copy=cc.ChunkCacheStore();copy.restore(store.snapshot());assert copy.to_dict()==store.to_dict()


@pytest.mark.parametrize("payload",["{","[]","not json"])
def test_malformed_serialization_rejected(payload):
    with pytest.raises(cc.ChunkCacheValidationError):cc.deserialize_cache_store(payload)


def test_unknown_schema_and_duplicate_completed_are_rejected():
    store,entry=completed();data=json.loads(cc.serialize_cache_store(store));data["schema_version"]="999"
    with pytest.raises(cc.ChunkCacheValidationError):cc.deserialize_cache_store(json.dumps(data))


def test_file_store_requires_allowed_root_and_rejects_all_escape_forms(tmp_path):
    store,_=completed()
    allowed_root=tmp_path/"cache"
    outside_root=tmp_path/"outside"
    outside_root.mkdir()
    valid=allowed_root/"cache.json"
    cc.save_cache_store(valid,store,allowed_root=allowed_root)
    assert cc.load_cache_store(valid,allowed_root=allowed_root).to_dict()==store.to_dict()
    with pytest.raises(TypeError):cc.save_cache_store(valid,store)
    with pytest.raises(TypeError):cc.load_cache_store(valid)
    with pytest.raises(cc.ChunkCacheValidationError):cc.save_cache_store(allowed_root,store,allowed_root=allowed_root)
    with pytest.raises(cc.ChunkCacheValidationError):cc.save_cache_store(outside_root/"cache.json",store,allowed_root=allowed_root)
    with pytest.raises(cc.ChunkCacheValidationError):cc.save_cache_store(allowed_root/".."/"escape.json",store,allowed_root=allowed_root)
    with pytest.raises(cc.ChunkCacheValidationError):cc.save_cache_store(outside_root.resolve()/"absolute-cache.json",store,allowed_root=allowed_root)
    link=allowed_root/"link"
    try:
        link.symlink_to(outside_root,target_is_directory=True)
    except OSError:
        return
    with pytest.raises(cc.ChunkCacheValidationError):cc.save_cache_store(link/"cache.json",store,allowed_root=allowed_root)
    data=json.loads(cc.serialize_cache_store(store));copy=dict(data["entries"][0]);copy["cache_entry_id"]="cache-duplicate";data["entries"].append(copy)
    with pytest.raises(cc.ChunkCacheValidationError):cc.deserialize_cache_store(json.dumps(data))


def test_retention_is_explicit_and_keeps_tombstone_evidence():
    store=cc.ChunkCacheStore()
    for index in range(5):completed(store,index+1)
    plan=cc.plan_cache_retention(store,policy=cc.RetentionPolicy(maximum_entries=3),current_time=T2);assert len(plan.remove_entry_ids)==2;cc.apply_cache_retention(store,plan,applied_at=T2);assert len(store.entries)==3 and len(store.retention_log)==2;assert all("translation_hash" in x for x in store.retention_log)


def test_output_contract_rejects_partial_and_detects_order_duplicate_missing():
    store,one=completed(index=1);_,two=completed(store,index=2);results=[cc.build_cached_chunk_result(one),cc.build_cached_chunk_result(two)];assert cc.validate_cached_chunk_for_output(results,document_id="doc-1",expected_chunk_indexes=(1,2))["valid"]
    invalid=cc.validate_cached_chunk_for_output((results[1],results[0],results[0]),document_id="doc-1",expected_chunk_indexes=(1,2,3));assert not invalid["valid"] and invalid["duplicates"]==[1] and invalid["missing"]==[3]
    failed_store=cc.ChunkCacheStore();prepared=cc.create_cache_entry(identity(),created_at=T0);cc.add_cache_entry(failed_store,prepared);partial=cc.record_cache_failure(failed_store,prepared.cache_entry_id,status="partial",failure_type="partial",attempt_count=1,failure_ttl=60,updated_at=T1,partial_text="片段")
    with pytest.raises(cc.ChunkCacheValidationError):cc.build_cached_chunk_result(partial)


def test_public_api_has_no_runtime_provider_or_cli_execution():
    assert len(cc.__all__)<70;assert not {"execute_provider","run_runtime","translate","assemble_output"}&set(cc.__all__)
