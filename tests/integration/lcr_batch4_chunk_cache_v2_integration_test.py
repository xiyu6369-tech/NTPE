from __future__ import annotations
import ast,hashlib,subprocess
from pathlib import Path
import core.chunk_cache_v2 as cc
from core.translation_scheduler import JobStatus,TranslationCollector,TranslationJob

ROOT=Path(__file__).resolve().parents[2];T0="2026-07-16T00:00:00Z";T1="2026-07-16T00:01:00Z";T2="2026-07-16T00:02:00Z"
def identity(index=1,**changes):
    values=dict(source_text=f"source {index}",prompt="prompt",system_prompt="system",policy={"v":1},context_selection=["ctx"],glossary={"v":1},character_memory_selection_fingerprint=cc.sha256_text("char"),context_scene_selection_fingerprint=cc.sha256_text("scene"),language_profile_id="profile",language_profile_version="1",source_language="ko",target_language="zh-TW",provider_id="offline-id",model_id="model",provider_request_profile={"timeout":30},generation_settings={"temperature":0},quality_policy_id="quality",quality_policy_version="1",translation_engine_version="7.2",chunk_index=index,document_id="doc-1",chunking_strategy_id="paragraph",chunking_strategy_version="1",context_token_budget=512);values.update(changes);return cc.create_cache_identity(**values)
def add_completed(store,index):
    entry=cc.create_cache_entry(identity(index),created_at=T0);cc.add_cache_entry(store,entry);return cc.complete_cache_entry(store,entry.cache_entry_id,translation_text=f"translated {index}",quality_status="passed",quality_evidence=({"gate":"pass"},),completed_at=T1)
def resume(entry,status="DONE",**changes):
    value={"chunk_index":entry.chunk_index,"document_id":entry.document_id,"status":status,"translation_hash":entry.translation_hash,"prompt_hash":entry.prompt_hash};value.update(changes);return value


def test_resume_reconciliation_matrix_is_fail_closed():
    store=cc.ChunkCacheStore();entry=add_completed(store,1)
    assert cc.reconcile_cache_with_resume(entry,resume(entry)).status==cc.ReconciliationStatus.CONSISTENT
    assert cc.reconcile_cache_with_resume(entry,None).status==cc.ReconciliationStatus.CACHE_ONLY
    assert cc.reconcile_resume_only({"chunk_index":1}).status==cc.ReconciliationStatus.RESUME_ONLY
    assert cc.reconcile_cache_with_resume(entry,resume(entry,status="FAILED")).status==cc.ReconciliationStatus.RETRY_REQUIRED
    assert cc.reconcile_cache_with_resume(entry,resume(entry,translation_hash="0"*64)).status==cc.ReconciliationStatus.CONFLICT
    assert cc.reconcile_cache_with_resume(entry,resume(entry,document_id="other")).status==cc.ReconciliationStatus.INVALID
    assert cc.reconcile_cache_with_resume(entry,resume(entry,prompt_hash="0"*64)).status==cc.ReconciliationStatus.STALE


def test_cached_result_matches_existing_collector_contract_without_reimplementation():
    store=cc.ChunkCacheStore();entries=[add_completed(store,i) for i in range(1,4)];collector=TranslationCollector(chunks_total=3)
    for result in map(cc.build_cached_chunk_result,entries):
        job=TranslationJob(job_id=f"cached-{result.chunk_index}",chunk_index=result.chunk_index,source_text="");job.status=JobStatus.DONE;job.result=result.translation_text;assert collector.collect(job)
    assert collector.merge_results()=="translated 1\ntranslated 2\ntranslated 3";assert collector.build_manifest()["merge_ready"]


def test_retry_plan_reuses_eight_and_retries_timeout_and_missing_only():
    store=cc.ChunkCacheStore();resume_state={}
    for index in range(1,9):entry=add_completed(store,index);resume_state[index]=resume(entry)
    timeout=cc.create_cache_entry(identity(9),created_at=T0);cc.add_cache_entry(store,timeout);cc.record_cache_failure(store,timeout.cache_entry_id,status="timeout",failure_type="timeout",attempt_count=2,failure_ttl=60,updated_at=T1)
    plan=cc.plan_chunk_reexecution([identity(i) for i in range(1,11)],store,resume_state,current_time=T2)
    assert plan.reusable_chunks==tuple(range(1,9));assert plan.retry_chunks==(9,10);assert not plan.invalid_chunks and not plan.conflicts


def test_selected_memory_fingerprints_not_full_store_drive_identity():
    base=identity();unselected_store_change=identity();selected_character_change=replace_identity(base,character_memory_selection_fingerprint=cc.sha256_text("changed-char"));selected_scene_change=replace_identity(base,context_scene_selection_fingerprint=cc.sha256_text("changed-scene"))
    assert cc.cache_key_for_identity(base)==cc.cache_key_for_identity(unselected_store_change)
    assert cc.cache_key_for_identity(base)!=cc.cache_key_for_identity(selected_character_change)
    assert cc.cache_key_for_identity(base)!=cc.cache_key_for_identity(selected_scene_change)


def replace_identity(item,**changes):
    values=item.to_dict();values.update(changes);return cc.CacheIdentity.from_dict(values)


def test_document_chunk_policy_and_engine_invalidation_are_scoped():
    store=cc.ChunkCacheStore();entries=[add_completed(store,i) for i in range(1,4)]
    changed=cc.invalidate_cache_entries(store,reason="policy-version",document_id="doc-1",chunk_index=2,quality_policy_version="1",invalidated_at=T2)
    assert [x.chunk_index for x in changed]==[2];assert store.get(entries[0].cache_entry_id).status==cc.CacheStatus.COMPLETED;assert store.get(entries[1].cache_entry_id).invalidated_reason=="policy-version"


def test_atomic_file_roundtrip_uses_pytest_temp_directory(tmp_path):
    store=cc.ChunkCacheStore();add_completed(store,1);root=tmp_path/"cache-root";path=root/"cache.json";cc.save_cache_store(path,store,allowed_root=root);assert cc.load_cache_store(path,allowed_root=root).to_dict()==store.to_dict();assert not path.with_name(path.name+".tmp").exists()


def test_chunk_cache_has_no_runtime_provider_prompt_or_network_imports():
    forbidden={"requests","httpx","urllib","socket"};fragments=("production_runtime","ai_provider","prompt_builder","translation_pipeline")
    for path in (ROOT/"core"/"chunk_cache_v2").glob("*.py"):
        tree=ast.parse(path.read_text(encoding="utf-8"));names=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):names.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):names.append(node.module or "")
        assert not forbidden&{x.split(".")[0] for x in names};assert not any(fragment in name for name in names for fragment in fragments)


def test_frozen_batch2_batch3_resume_and_output_core_match_head():
    roots=("core/character_memory_v2/","core/context_scene_memory/","core/translation_scheduler/journal.py","core/translation_scheduler/collector.py")
    files=subprocess.run(["git","-c","core.quotepath=false","ls-files"],cwd=ROOT,check=True,capture_output=True,text=True,encoding="utf-8").stdout.splitlines()
    for relative in [p for p in files if p.startswith(roots) or p in roots]:
        assert (ROOT/relative).read_bytes()==subprocess.run(["git","show",f"HEAD:{relative}"],cwd=ROOT,check=True,capture_output=True).stdout


def test_batch4_worktree_allowlist_only():
    allowed=("core/chunk_cache_v2/","tests/unit/test_chunk_cache_v2.py","tests/integration/lcr_batch4_chunk_cache_v2_integration_test.py","ntpe_lcr_batch4_chunk_cache_v2_test.py","audits/legacy_capability_recovery/batch4/")
    lines=subprocess.run(["git","status","--short"],cwd=ROOT,check=True,capture_output=True,text=True,encoding="utf-8").stdout.splitlines()
    assert all(line[3:].replace("\\","/").startswith(allowed) for line in lines)
