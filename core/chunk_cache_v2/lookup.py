from __future__ import annotations
from dataclasses import replace
from datetime import datetime,timezone
from .fingerprint import cache_key_for_identity,sha256_text
from .models import CachePolicy,CacheStatus,ExpiryKind,LookupDecision,LookupResult,QualityStatus
from .store import ChunkCacheStore
from .validation import ChunkCacheValidationError,parse_timestamp,validate_entry

_CHANGE_REASONS=(("source_hash","source_changed"),("normalized_source_hash","source_changed"),("prompt_hash","prompt_changed"),("system_prompt_hash","prompt_changed"),("policy_hash","prompt_changed"),("context_hash","context_changed"),("character_memory_selection_fingerprint","context_changed"),("context_scene_selection_fingerprint","context_changed"),("context_token_budget","context_changed"),("glossary_hash","glossary_changed"),("provider_id","provider_changed"),("provider_request_profile_hash","provider_changed"),("model_id","model_changed"),("generation_settings_hash","generation_settings_changed"),("quality_policy_id","quality_policy_changed"),("quality_policy_version","quality_policy_changed"),("language_profile_id","language_profile_changed"),("language_profile_version","language_profile_changed"),("translation_engine_version","engine_version_changed"))


def lookup_chunk_cache(store:ChunkCacheStore,identity,*,cache_policy=None,current_time=None):
    policy=cache_policy or CachePolicy();key=cache_key_for_identity(identity);now=datetime.now(timezone.utc) if current_time is None else parse_timestamp(current_time,"current_time")
    exact=list(store.find_by_cache_key(key))
    if not exact:
        related=[x for x in store.entries.values() if x.document_id==identity.document_id and x.chunk_index==identity.chunk_index]
        if not related:return LookupResult(LookupDecision.MISS,None,"not_found",None,{"identity":False})
        candidate=max(related,key=lambda x:(x.version,x.updated_at))
        for field,reason in _CHANGE_REASONS:
            if getattr(candidate.identity,field)!=getattr(identity,field):return LookupResult(LookupDecision.STALE,candidate,reason,candidate.cache_key,{"identity":False})
        return LookupResult(LookupDecision.STALE,candidate,"identity_mismatch",candidate.cache_key,{"identity":False})
    completed=[x for x in exact if x.status==CacheStatus.COMPLETED]
    if len(completed)>1:return LookupResult(LookupDecision.CONFLICT,None,"corrupt_entry",key,{"unique":False})
    entry=max(exact,key=lambda x:(x.version,x.updated_at))
    projections_ok=entry.identity==identity and entry.cache_key==key and entry.document_id==identity.document_id and entry.chunk_index==identity.chunk_index and entry.source_hash==identity.source_hash and entry.prompt_hash==identity.prompt_hash and entry.provider_id==identity.provider_id and entry.model_id==identity.model_id
    if not projections_ok:return LookupResult(LookupDecision.INVALID,entry,"corrupt_entry",key,{"integrity":False})
    if entry.expiry_policy.kind==ExpiryKind.TIMESTAMP and now>=parse_timestamp(entry.expiry_policy.expires_at or "","expires_at"):return LookupResult(LookupDecision.STALE,entry,"expired",key,{"expiry":False})
    if entry.expiry_policy.kind==ExpiryKind.ACCESS_BASED and entry.expiry_policy.max_idle_seconds is not None:
        accessed=parse_timestamp(entry.last_accessed_at or entry.updated_at,"last_accessed_at")
        if (now-accessed).total_seconds()>entry.expiry_policy.max_idle_seconds:return LookupResult(LookupDecision.STALE,entry,"expired",key,{"expiry":False})
    if entry.status in {CacheStatus.PARTIAL,CacheStatus.FAILED,CacheStatus.TIMEOUT}:return LookupResult(LookupDecision.RETRY_REQUIRED,entry,{CacheStatus.PARTIAL:"partial_entry",CacheStatus.FAILED:"failed_entry",CacheStatus.TIMEOUT:"timeout_entry"}[entry.status],key,{"completed":False})
    if entry.status in {CacheStatus.CANCELLED,CacheStatus.INVALID}:return LookupResult(LookupDecision.INVALID,entry,"corrupt_entry" if entry.status==CacheStatus.INVALID else "failed_entry",key,{"completed":False})
    if entry.status in {CacheStatus.STALE,CacheStatus.SUPERSEDED,CacheStatus.ROLLED_BACK}:return LookupResult(LookupDecision.STALE,entry,entry.invalidated_reason or "manual_invalidation",key,{"current":False})
    if entry.status!=CacheStatus.COMPLETED:return LookupResult(LookupDecision.INELIGIBLE,entry,"quality_not_evaluated",key,{"completed":False})
    if entry.translation_hash!=sha256_text(entry.translation_text or ""):return LookupResult(LookupDecision.INVALID,entry,"translation_hash_mismatch",key,{"translation_hash":False})
    if entry.quality_status==QualityStatus.FAILED:return LookupResult(LookupDecision.INELIGIBLE,entry,"quality_failed",key,{"quality":False})
    allowed=entry.quality_status==QualityStatus.PASSED or (policy.allow_nonblocking_issues and entry.quality_status==QualityStatus.PASSED_WITH_NONBLOCKING_ISSUES)
    if not allowed:return LookupResult(LookupDecision.INELIGIBLE,entry,"quality_not_evaluated",key,{"quality":False})
    accessed=(current_time or datetime.now(timezone.utc).isoformat().replace("+00:00","Z"));store.entries[entry.cache_entry_id]=replace(entry,last_accessed_at=accessed,hit_count=entry.hit_count+1,updated_at=accessed);store.snapshot_version+=1
    return LookupResult(LookupDecision.HIT,store.get(entry.cache_entry_id),"eligible_completed",key,{"identity":True,"translation_hash":True,"quality":True,"completed":True})
