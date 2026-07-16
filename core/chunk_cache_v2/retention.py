from __future__ import annotations
from datetime import datetime,timezone
from .models import CacheStatus,RetentionPlan,RetentionPolicy
from .validation import parse_timestamp


def plan_cache_retention(store,*,policy=None,current_time=None):
    policy=policy or RetentionPolicy();now=datetime.now(timezone.utc) if current_time is None else parse_timestamp(current_time,"current_time");remove={};by_key={}
    for entry in store.entries.values():by_key.setdefault(entry.cache_key,[]).append(entry)
    for entries in by_key.values():
        for entry in sorted(entries,key=lambda x:(x.version,x.updated_at),reverse=True)[policy.maximum_versions_per_cache_key:]:remove[entry.cache_entry_id]="version_limit"
    for entry in store.entries.values():
        age=(now-parse_timestamp(entry.updated_at,"updated_at")).total_seconds()
        limit=policy.failure_max_age_seconds if entry.status in {CacheStatus.FAILED,CacheStatus.TIMEOUT,CacheStatus.PARTIAL,CacheStatus.CANCELLED} else policy.maximum_age_seconds
        if limit is not None and age>limit:remove[entry.cache_entry_id]="age_limit"
    remaining=[x for x in store.entries.values() if x.cache_entry_id not in remove]
    overflow=max(0,len(remaining)-policy.maximum_entries)
    for entry in sorted(remaining,key=lambda x:x.updated_at)[:overflow]:remove[entry.cache_entry_id]="entry_limit"
    retain=tuple(sorted(set(store.entries)-set(remove)));return RetentionPlan(tuple(sorted(remove)),retain,dict(sorted(remove.items())))


def apply_cache_retention(store,plan,*,applied_at):
    for entry_id in plan.remove_entry_ids:
        entry=store.entries.pop(entry_id);store._cache_index.get(entry.cache_key,set()).discard(entry_id);store.history.pop(entry_id,None);store.retention_log.append({"cache_entry_id":entry_id,"cache_key":entry.cache_key,"status":entry.status.value,"translation_hash":entry.translation_hash,"reason":plan.reasons[entry_id],"applied_at":applied_at})
        store.snapshot_version+=1
    return tuple(plan.remove_entry_ids)
