from __future__ import annotations
import re
from datetime import datetime
from typing import Any
from .fingerprint import cache_key_for_identity, sha256_text
from .models import CacheEntry, CacheIdentity, CacheStatus, ExpiryKind, QualityStatus, SCHEMA_VERSION


class ChunkCacheValidationError(ValueError): pass
_SHA=re.compile(r"^[0-9a-f]{64}$",re.I); _ID=re.compile(r"^[A-Za-z0-9._:-]{1,180}$")
_SECRET=(re.compile(r"nvapi-[A-Za-z0-9._-]{16,}",re.I),re.compile(r"Bearer\s+[A-Za-z0-9._-]{12,}",re.I),re.compile(r"Authorization\s*:\s*\S+",re.I),re.compile(r"api[_-]?key\s*=\s*\S+",re.I),re.compile(r"-----BEGIN .*PRIVATE KEY-----",re.I))


def parse_timestamp(value:str,name:str)->datetime:
    try: result=datetime.fromisoformat(value.replace("Z","+00:00"))
    except (AttributeError,ValueError) as exc: raise ChunkCacheValidationError(f"{name} must be ISO-8601") from exc
    if result.tzinfo is None: raise ChunkCacheValidationError(f"{name} must include timezone")
    return result


def safe_id(value:str,name:str)->None:
    if not isinstance(value,str) or not _ID.fullmatch(value) or value in {".",".."} or "/" in value or "\\" in value: raise ChunkCacheValidationError(f"invalid {name}")
    if any(p.search(value) for p in _SECRET): raise ChunkCacheValidationError(f"secret-like {name}")


def validate_identity(identity:CacheIdentity)->None:
    for name in ("source_hash","normalized_source_hash","prompt_hash","system_prompt_hash","policy_hash","context_hash","glossary_hash","character_memory_selection_fingerprint","context_scene_selection_fingerprint","provider_request_profile_hash","generation_settings_hash"):
        if not _SHA.fullmatch(getattr(identity,name)): raise ChunkCacheValidationError(f"{name} must be SHA-256")
    for name in ("language_profile_id","language_profile_version","source_language","target_language","provider_id","model_id","quality_policy_id","quality_policy_version","translation_engine_version","document_id","chunking_strategy_id","chunking_strategy_version"): safe_id(getattr(identity,name),name)
    if identity.chunk_index<0 or identity.context_token_budget<0: raise ChunkCacheValidationError("negative identity numeric field")


def validate_entry(entry:CacheEntry, *, require_completed_integrity:bool=True)->None:
    validate_identity(entry.identity); safe_id(entry.cache_entry_id,"cache_entry_id")
    if cache_key_for_identity(entry.identity)!=entry.cache_key: raise ChunkCacheValidationError("cache_key mismatch")
    if entry.document_id!=entry.identity.document_id or entry.chunk_index!=entry.identity.chunk_index or entry.source_hash!=entry.identity.source_hash or entry.prompt_hash!=entry.identity.prompt_hash or entry.provider_id!=entry.identity.provider_id or entry.model_id!=entry.identity.model_id: raise ChunkCacheValidationError("entry identity projection mismatch")
    for value,name in ((entry.created_at,"created_at"),(entry.updated_at,"updated_at")): parse_timestamp(value,name)
    for value,name in ((entry.completed_at,"completed_at"),(entry.last_accessed_at,"last_accessed_at"),(entry.retry_after,"retry_after")):
        if value is not None: parse_timestamp(value,name)
    if entry.version<1 or entry.hit_count<0 or entry.attempt_count<0: raise ChunkCacheValidationError("invalid counter")
    if entry.expiry_policy.kind==ExpiryKind.TIMESTAMP and not entry.expiry_policy.expires_at: raise ChunkCacheValidationError("timestamp expiry missing")
    if entry.expiry_policy.expires_at: parse_timestamp(entry.expiry_policy.expires_at,"expires_at")
    if entry.translation_text and any(p.search(entry.translation_text) for p in _SECRET): raise ChunkCacheValidationError("secret-like translation")
    if entry.translation_hash and (not _SHA.fullmatch(entry.translation_hash) or (entry.translation_text is not None and sha256_text(entry.translation_text)!=entry.translation_hash)): raise ChunkCacheValidationError("translation_hash mismatch")
    if require_completed_integrity and entry.status==CacheStatus.COMPLETED:
        if not entry.translation_text or not entry.translation_hash or entry.quality_status not in {QualityStatus.PASSED,QualityStatus.PASSED_WITH_NONBLOCKING_ISSUES} or not entry.validation_passed or entry.partial or entry.timeout or entry.cancelled or not entry.completed_at: raise ChunkCacheValidationError("invalid completed entry")


def validate_cache_store(store:Any)->dict[str,Any]:
    errors=[]; active={}
    if getattr(store,"schema_version",None)!=SCHEMA_VERSION: errors.append("unknown schema_version")
    for key,entry in getattr(store,"entries",{}).items():
        try:
            if key!=entry.cache_entry_id: raise ChunkCacheValidationError("entry key mismatch")
            validate_entry(entry)
            if entry.status==CacheStatus.COMPLETED:
                if entry.cache_key in active: raise ChunkCacheValidationError("duplicate active completed entry")
                active[entry.cache_key]=entry.cache_entry_id
        except (ValueError,TypeError) as exc: errors.append(f"{key}: {exc}")
    return {"valid":not errors,"errors":errors,"entry_count":len(getattr(store,"entries",{})),"schema_version":getattr(store,"schema_version",None)}
