from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class SingleChunkExecutionTarget:
    document_id: str
    chunk_id: str
    chunk_index: int
    source_text: str
    source_hash: str
    production_translation: str
    production_translation_hash: str
    rollback_baseline_hash: str
    source_profile: str
    target_profile: str
    bounded_context: Mapping[str, object]
    glossary_subset: Mapping[str, str]


@dataclass(frozen=True)
class ExecutionReviewResult:
    status: str
    outcome: str
    reason_codes: tuple[str, ...]
    provider_requests: int
    network_requests: int
    request_evidence: tuple[Mapping[str, object], ...]
    semantic_status: str
    artifact_path: str | None
    artifact_hash: str | None
    rollback_used: bool
    production_translation_retained: bool = True
    formal_translation_replaced: bool = False
    formal_output_modified: bool = False
    resume_modified: bool = False
    production_cache_modified: bool = False
    character_store_modified: bool = False
    context_store_modified: bool = False
    automatic_rollout: bool = False
    active_production_authorized: bool = False
    retry_count: int = 0
    fallback_used: bool = False
