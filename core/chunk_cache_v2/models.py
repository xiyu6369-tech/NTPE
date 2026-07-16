from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

SCHEMA_VERSION = "2.0"


class CacheStatus(str, Enum):
    PREPARED="prepared"; IN_PROGRESS="in_progress"; COMPLETED="completed"; PARTIAL="partial"; FAILED="failed"; TIMEOUT="timeout"; CANCELLED="cancelled"; INVALID="invalid"; STALE="stale"; SUPERSEDED="superseded"; ROLLED_BACK="rolled_back"


class QualityStatus(str, Enum):
    PASSED="passed"; PASSED_WITH_NONBLOCKING_ISSUES="passed_with_nonblocking_issues"; FAILED="failed"; NOT_EVALUATED="not_evaluated"; INSUFFICIENT_EVIDENCE="insufficient_evidence"; INVALID="invalid"


class LookupDecision(str, Enum):
    HIT="hit"; MISS="miss"; STALE="stale"; INELIGIBLE="ineligible"; CONFLICT="conflict"; INVALID="invalid"; RETRY_REQUIRED="retry_required"


class ReconciliationStatus(str, Enum):
    CONSISTENT="consistent"; CACHE_ONLY="cache_only"; RESUME_ONLY="resume_only"; CONFLICT="conflict"; STALE="stale"; RETRY_REQUIRED="retry_required"; INVALID="invalid"


class ExpiryKind(str, Enum):
    NEVER="never"; TIMESTAMP="timestamp"; ACCESS_BASED="access_based"; VERSION_BASED="version_based"; MANUAL_REVIEW_REQUIRED="manual_review_required"


@dataclass(frozen=True)
class CacheIdentity:
    source_hash: str; normalized_source_hash: str; prompt_hash: str; system_prompt_hash: str
    policy_hash: str; context_hash: str; glossary_hash: str
    character_memory_selection_fingerprint: str; context_scene_selection_fingerprint: str
    language_profile_id: str; language_profile_version: str; source_language: str; target_language: str
    provider_id: str; model_id: str; provider_request_profile_hash: str; generation_settings_hash: str
    quality_policy_id: str; quality_policy_version: str; translation_engine_version: str
    chunk_index: int; document_id: str; chunking_strategy_id: str; chunking_strategy_version: str
    context_token_budget: int

    def to_dict(self) -> dict[str, Any]: return {name: getattr(self, name) for name in self.__dataclass_fields__}
    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CacheIdentity": return cls(**{name: data[name] for name in cls.__dataclass_fields__})


@dataclass(frozen=True)
class ExpiryPolicy:
    kind: ExpiryKind; expires_at: str|None=None; max_idle_seconds: int|None=None; max_versions: int|None=None
    def to_dict(self): return {"kind":self.kind.value,"expires_at":self.expires_at,"max_idle_seconds":self.max_idle_seconds,"max_versions":self.max_versions}
    @classmethod
    def from_dict(cls,d): return cls(ExpiryKind(d["kind"]),d.get("expires_at"),d.get("max_idle_seconds"),d.get("max_versions"))


@dataclass(frozen=True)
class CacheEntry:
    cache_entry_id: str; cache_key: str; identity: CacheIdentity; document_id: str; chunk_index: int
    source_hash: str; prompt_hash: str; provider_id: str; model_id: str; source_language: str; target_language: str
    status: CacheStatus; translation_text: str|None; translation_hash: str|None; quality_status: QualityStatus
    quality_evidence: tuple[Mapping[str,Any],...]; provider_attempt_summary: Mapping[str,Any]
    created_at: str; updated_at: str; completed_at: str|None; last_accessed_at: str|None; hit_count: int; version: int
    expiry_policy: ExpiryPolicy; invalidated_reason: str|None; parent_entry_id: str|None
    validation_passed: bool; partial: bool; timeout: bool; cancelled: bool
    failure_ttl: int|None; retry_after: str|None; attempt_count: int; last_failure_type: str|None

    def to_dict(self):
        value={name:getattr(self,name) for name in self.__dataclass_fields__}; value["identity"]=self.identity.to_dict(); value["status"]=self.status.value; value["quality_status"]=self.quality_status.value; value["quality_evidence"]=[dict(x) for x in self.quality_evidence]; value["provider_attempt_summary"]=dict(self.provider_attempt_summary); value["expiry_policy"]=self.expiry_policy.to_dict(); return value
    @classmethod
    def from_dict(cls,d):
        value=dict(d); value["identity"]=CacheIdentity.from_dict(value["identity"]); value["status"]=CacheStatus(value["status"]); value["quality_status"]=QualityStatus(value["quality_status"]); value["quality_evidence"]=tuple(value["quality_evidence"]); value["expiry_policy"]=ExpiryPolicy.from_dict(value["expiry_policy"]); return cls(**value)


@dataclass(frozen=True)
class CachePolicy:
    allow_nonblocking_issues: bool=False


@dataclass(frozen=True)
class LookupResult:
    decision: LookupDecision; entry: CacheEntry|None; reason: str; matched_cache_key: str|None; validation_results: Mapping[str,bool]


@dataclass(frozen=True)
class ReconciliationResult:
    status: ReconciliationStatus; reason: str; cache_entry_id: str|None; chunk_index: int|None


@dataclass(frozen=True)
class CachedChunkResult:
    chunk_index: int; document_id: str; translation_text: str; translation_hash: str; completion_status: str; source_hash: str; prompt_hash: str; cache_entry_id: str


@dataclass(frozen=True)
class ReexecutionPlan:
    reusable_chunks: tuple[int,...]; retry_chunks: tuple[int,...]; invalid_chunks: tuple[int,...]; conflicts: tuple[int,...]; reasons: Mapping[int,str]


@dataclass(frozen=True)
class RetentionPolicy:
    maximum_entries: int=10000; maximum_age_seconds: int|None=None; maximum_versions_per_cache_key: int=3; failure_max_age_seconds: int=86400


@dataclass(frozen=True)
class RetentionPlan:
    remove_entry_ids: tuple[str,...]; retain_entry_ids: tuple[str,...]; reasons: Mapping[str,str]
