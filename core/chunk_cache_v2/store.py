from __future__ import annotations
from dataclasses import replace
from datetime import datetime,timezone
from typing import Any,Mapping
from .fingerprint import cache_key_for_identity
from .models import CacheEntry,CacheIdentity,CacheStatus,ExpiryKind,ExpiryPolicy,QualityStatus,SCHEMA_VERSION
from .validation import ChunkCacheValidationError,validate_cache_store,validate_entry


def utc_now()->str:return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")


class ChunkCacheStore:
    def __init__(self): self.schema_version=SCHEMA_VERSION; self.entries={}; self.history={}; self.retention_log=[]; self.snapshot_version=0; self._cache_index={}
    def get(self,entry_id):
        try:return self.entries[entry_id]
        except KeyError as exc:raise ChunkCacheValidationError(f"unknown cache_entry_id: {entry_id}") from exc
    def _insert(self,entry):
        validate_entry(entry)
        if entry.cache_entry_id in self.entries:raise ChunkCacheValidationError("duplicate cache_entry_id")
        self.entries[entry.cache_entry_id]=entry;self._cache_index.setdefault(entry.cache_key,set()).add(entry.cache_entry_id);self.history.setdefault(entry.cache_entry_id,[]);self.snapshot_version+=1
    def _update(self,entry):
        validate_entry(entry);current=self.get(entry.cache_entry_id)
        if entry.version!=current.version+1:raise ChunkCacheValidationError("version must increment once")
        self.history.setdefault(entry.cache_entry_id,[]).append(current);self.entries[entry.cache_entry_id]=entry;self.snapshot_version+=1
    def find_by_cache_key(self,cache_key):return tuple(self.entries[x] for x in sorted(self._cache_index.get(cache_key,())))
    def snapshot(self):return self.to_dict()
    def restore(self,payload):
        other=self.from_dict(payload);self.schema_version=other.schema_version;self.entries=dict(other.entries);self.history={k:list(v) for k,v in other.history.items()};self.retention_log=list(other.retention_log);self.snapshot_version=other.snapshot_version;self._cache_index={k:set(v) for k,v in other._cache_index.items()}
    def to_dict(self):return {"schema_version":self.schema_version,"entries":[self.entries[k].to_dict() for k in sorted(self.entries)],"history":{k:[x.to_dict() for x in self.history[k]] for k in sorted(self.history)},"retention_log":list(self.retention_log),"snapshot_version":self.snapshot_version}
    @classmethod
    def from_dict(cls,payload:Mapping[str,Any]):
        if set(payload)!={"schema_version","entries","history","retention_log","snapshot_version"} or payload.get("schema_version")!=SCHEMA_VERSION:raise ChunkCacheValidationError("unknown schema or invalid store fields")
        store=cls()
        try:
            for raw in payload["entries"]:
                entry=CacheEntry.from_dict(raw)
                if entry.cache_entry_id in store.entries:raise ChunkCacheValidationError("duplicate serialized entry")
                store.entries[entry.cache_entry_id]=entry;store._cache_index.setdefault(entry.cache_key,set()).add(entry.cache_entry_id)
            store.history={str(k):[CacheEntry.from_dict(x) for x in values] for k,values in payload["history"].items()};store.retention_log=list(payload["retention_log"]);store.snapshot_version=int(payload["snapshot_version"])
        except (KeyError,TypeError,ValueError) as exc:raise ChunkCacheValidationError("invalid cache store payload") from exc
        result=validate_cache_store(store)
        if not result["valid"]:raise ChunkCacheValidationError("; ".join(result["errors"]))
        return store


def create_cache_entry(identity:CacheIdentity,*,created_at:str|None=None,expiry_policy:ExpiryPolicy|None=None,parent_entry_id:str|None=None,cache_entry_id:str|None=None)->CacheEntry:
    timestamp=created_at or utc_now();key=cache_key_for_identity(identity);entry_id=cache_entry_id or f"cache-{key[:24]}-v1"
    entry=CacheEntry(entry_id,key,identity,identity.document_id,identity.chunk_index,identity.source_hash,identity.prompt_hash,identity.provider_id,identity.model_id,identity.source_language,identity.target_language,CacheStatus.PREPARED,None,None,QualityStatus.NOT_EVALUATED,(),{},timestamp,timestamp,None,None,0,1,expiry_policy or ExpiryPolicy(ExpiryKind.NEVER),None,parent_entry_id,False,False,False,False,None,None,0,None)
    validate_entry(entry);return entry


def add_cache_entry(store:ChunkCacheStore,entry:CacheEntry)->CacheEntry:
    active=[x for x in store.entries.values() if x.cache_key==entry.cache_key and x.status==CacheStatus.COMPLETED]
    if active:raise ChunkCacheValidationError("active completed entry already exists for cache key")
    store._insert(entry);return entry
