from __future__ import annotations
from typing import Mapping,Sequence,Any
from .fingerprint import cache_key_for_identity
from .lookup import lookup_chunk_cache
from .models import CacheStatus,CachedChunkResult,LookupDecision,ReconciliationResult,ReconciliationStatus,ReexecutionPlan
from .validation import ChunkCacheValidationError,validate_entry


def reconcile_cache_with_resume(cache_entry,resume_record:Mapping[str,Any]|None):
    if resume_record is None:return ReconciliationResult(ReconciliationStatus.CACHE_ONLY,"resume_missing",cache_entry.cache_entry_id,cache_entry.chunk_index)
    if int(resume_record.get("chunk_index",-1))!=cache_entry.chunk_index or resume_record.get("document_id") not in {None,cache_entry.document_id}:return ReconciliationResult(ReconciliationStatus.INVALID,"document_identity_mismatch",cache_entry.cache_entry_id,cache_entry.chunk_index)
    status=str(resume_record.get("status","")).lower()
    if cache_entry.status!=CacheStatus.COMPLETED:return ReconciliationResult(ReconciliationStatus.RETRY_REQUIRED,"cache_not_completed",cache_entry.cache_entry_id,cache_entry.chunk_index)
    if status not in {"done","completed"}:return ReconciliationResult(ReconciliationStatus.RETRY_REQUIRED if status in {"failed","retry"} else ReconciliationStatus.CONFLICT,"resume_not_completed",cache_entry.cache_entry_id,cache_entry.chunk_index)
    if resume_record.get("translation_hash")!=cache_entry.translation_hash:return ReconciliationResult(ReconciliationStatus.CONFLICT,"translation_hash_mismatch",cache_entry.cache_entry_id,cache_entry.chunk_index)
    if resume_record.get("prompt_hash") not in {None,cache_entry.prompt_hash}:return ReconciliationResult(ReconciliationStatus.STALE,"prompt_identity_mismatch",cache_entry.cache_entry_id,cache_entry.chunk_index)
    return ReconciliationResult(ReconciliationStatus.CONSISTENT,"hashes_match",cache_entry.cache_entry_id,cache_entry.chunk_index)


def reconcile_resume_only(resume_record):return ReconciliationResult(ReconciliationStatus.RESUME_ONLY,"cache_missing",None,int(resume_record.get("chunk_index",-1)))


def build_cached_chunk_result(entry):
    validate_entry(entry)
    if entry.status!=CacheStatus.COMPLETED:raise ChunkCacheValidationError("only completed cache can build chunk result")
    return CachedChunkResult(entry.chunk_index,entry.document_id,entry.translation_text or "",entry.translation_hash or "","DONE",entry.source_hash,entry.prompt_hash,entry.cache_entry_id)


def validate_cached_chunk_for_output(results:Sequence[CachedChunkResult],*,document_id:str,expected_chunk_indexes:Sequence[int]):
    indexes=[x.chunk_index for x in results];duplicates=sorted({x for x in indexes if indexes.count(x)>1});missing=sorted(set(expected_chunk_indexes)-set(indexes));wrong=sorted(x.chunk_index for x in results if x.document_id!=document_id)
    return {"valid":not duplicates and not missing and not wrong and indexes==sorted(indexes),"duplicates":duplicates,"missing":missing,"wrong_document":wrong,"ordered":indexes==sorted(indexes)}


def plan_chunk_reexecution(document_chunks:Sequence[Any],cache_store,resume_state:Mapping[int,Mapping[str,Any]]|None=None,current_time=None):
    reusable=[];retry=[];invalid=[];conflicts=[];reasons={};resume_state=resume_state or {}
    for identity in document_chunks:
        result=lookup_chunk_cache(cache_store,identity,current_time=current_time)
        index=identity.chunk_index
        if result.decision==LookupDecision.HIT:
            reconciliation=reconcile_cache_with_resume(result.entry,resume_state.get(index))
            if reconciliation.status==ReconciliationStatus.CONSISTENT:reusable.append(index);reasons[index]="consistent"
            elif reconciliation.status==ReconciliationStatus.INVALID:invalid.append(index);reasons[index]=reconciliation.reason
            elif reconciliation.status==ReconciliationStatus.CONFLICT:conflicts.append(index);reasons[index]=reconciliation.reason
            else:retry.append(index);reasons[index]=reconciliation.reason
        elif result.decision==LookupDecision.CONFLICT:conflicts.append(index);reasons[index]=result.reason
        elif result.decision==LookupDecision.INVALID:invalid.append(index);reasons[index]=result.reason
        else:retry.append(index);reasons[index]=result.reason
    return ReexecutionPlan(tuple(sorted(reusable)),tuple(sorted(retry)),tuple(sorted(invalid)),tuple(sorted(conflicts)),reasons)
