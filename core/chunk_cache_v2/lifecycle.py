from __future__ import annotations
from dataclasses import replace
from .fingerprint import sha256_text
from .models import CacheStatus,QualityStatus
from .store import ChunkCacheStore,utc_now
from .validation import ChunkCacheValidationError,validate_entry


def complete_cache_entry(store:ChunkCacheStore,entry_id:str,*,translation_text:str,quality_status:QualityStatus|str,quality_evidence=(),provider_attempt_summary=None,completed_at:str|None=None,validation_passed:bool=True):
    current=store.get(entry_id)
    if current.status not in {CacheStatus.PREPARED,CacheStatus.IN_PROGRESS}:raise ChunkCacheValidationError("invalid completion transition")
    if not translation_text:raise ChunkCacheValidationError("completed translation must be non-empty")
    quality=quality_status if isinstance(quality_status,QualityStatus) else QualityStatus(quality_status);timestamp=completed_at or utc_now()
    updated=replace(current,status=CacheStatus.COMPLETED,translation_text=translation_text,translation_hash=sha256_text(translation_text),quality_status=quality,quality_evidence=tuple(quality_evidence),provider_attempt_summary=dict(provider_attempt_summary or {}),completed_at=timestamp,updated_at=timestamp,validation_passed=validation_passed,partial=False,timeout=False,cancelled=False,attempt_count=max(1,current.attempt_count),version=current.version+1)
    store._update(updated);return updated


def record_cache_failure(store:ChunkCacheStore,entry_id:str,*,status:CacheStatus|str,failure_type:str,attempt_count:int,failure_ttl:int,retry_after:str|None=None,evidence=(),updated_at:str|None=None,partial_text:str|None=None):
    kind=status if isinstance(status,CacheStatus) else CacheStatus(status)
    if kind not in {CacheStatus.PARTIAL,CacheStatus.FAILED,CacheStatus.TIMEOUT,CacheStatus.CANCELLED}:raise ChunkCacheValidationError("invalid failure status")
    current=store.get(entry_id);timestamp=updated_at or utc_now();updated=replace(current,status=kind,translation_text=partial_text if kind==CacheStatus.PARTIAL else None,translation_hash=sha256_text(partial_text) if partial_text else None,quality_status=QualityStatus.NOT_EVALUATED,quality_evidence=tuple(evidence),updated_at=timestamp,partial=kind==CacheStatus.PARTIAL,timeout=kind==CacheStatus.TIMEOUT,cancelled=kind==CacheStatus.CANCELLED,failure_ttl=failure_ttl,retry_after=retry_after,attempt_count=attempt_count,last_failure_type=failure_type,validation_passed=False,version=current.version+1)
    store._update(updated);return updated


def invalidate_cache_entry(store,entry_id,*,reason,invalidated_at=None,status=CacheStatus.STALE):
    current=store.get(entry_id);timestamp=invalidated_at or utc_now();kind=status if isinstance(status,CacheStatus) else CacheStatus(status)
    if kind not in {CacheStatus.STALE,CacheStatus.INVALID}:raise ChunkCacheValidationError("invalid invalidation status")
    updated=replace(current,status=kind,invalidated_reason=reason,updated_at=timestamp,version=current.version+1);store._update(updated);return updated


def invalidate_cache_entries(store,*,reason,document_id=None,chunk_index=None,cache_key=None,quality_policy_version=None,translation_engine_version=None,invalidated_at=None):
    changed=[]
    for entry in list(store.entries.values()):
        if entry.status in {CacheStatus.STALE,CacheStatus.INVALID,CacheStatus.SUPERSEDED}:continue
        if document_id is not None and entry.document_id!=document_id:continue
        if chunk_index is not None and entry.chunk_index!=chunk_index:continue
        if cache_key is not None and entry.cache_key!=cache_key:continue
        if quality_policy_version is not None and entry.identity.quality_policy_version!=quality_policy_version:continue
        if translation_engine_version is not None and entry.identity.translation_engine_version!=translation_engine_version:continue
        changed.append(invalidate_cache_entry(store,entry.cache_entry_id,reason=reason,invalidated_at=invalidated_at))
    return tuple(changed)


def supersede_cache_entry(store,entry_id,*,replacement_id,superseded_at=None):
    old=store.get(entry_id);new=store.get(replacement_id)
    if old.document_id!=new.document_id or old.chunk_index!=new.chunk_index:raise ChunkCacheValidationError("supersede scope mismatch")
    timestamp=superseded_at or utc_now();updated=replace(old,status=CacheStatus.SUPERSEDED,invalidated_reason=f"superseded_by:{replacement_id}",updated_at=timestamp,version=old.version+1);store._update(updated);return updated


def rollback_cache_entry(store,entry_id,*,target_version=None,current_identity=None,rolled_back_at=None):
    current=store.get(entry_id);history=list(store.history.get(entry_id,[]));candidates=history if target_version is None else [x for x in history if x.version==target_version]
    if not candidates:raise ChunkCacheValidationError("invalid rollback target")
    target=candidates[-1];timestamp=rolled_back_at or utc_now();status=target.status
    if current_identity is None or target.cache_key!=__import__("core.chunk_cache_v2.fingerprint",fromlist=["cache_key_for_identity"]).cache_key_for_identity(current_identity) or target.status!=CacheStatus.COMPLETED:status=CacheStatus.ROLLED_BACK
    restored=replace(target,status=status,updated_at=timestamp,version=current.version+1);store._update(restored);return restored
