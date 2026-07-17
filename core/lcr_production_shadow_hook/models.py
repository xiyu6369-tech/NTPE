from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


HOOK_VERSION = "lcr-batch10.3-hook-1.0"
HOOK_SYMBOL = "after_chunk_package_prepared"


@dataclass(frozen=True)
class HookEvidence:
    hook_id: str
    shadow_status: str
    input_fingerprint: str
    modules_evaluated: tuple[str, ...]
    provider_requests_executed: int
    production_output_changed: bool
    baseline_changed: bool
    warnings: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    result_discarded: bool
    duration_ms: float
    created_at: str
    character_memory: "CharacterMemoryShadowResult | None" = None
    context_scene: "ContextSceneShadowResult | None" = None


@dataclass(frozen=True)
class HookOutcome:
    status: str
    baseline_continues: bool
    evidence: HookEvidence | None
    before_hash: str
    after_hash: str
    prompt_before_hash: str
    prompt_after_hash: str
    provider_identity_before: str
    provider_identity_after: str
    resume_before_hash: str
    resume_after_hash: str
    output_contract_before_hash: str
    output_contract_after_hash: str
    warning_codes: tuple[str, ...] = ()
    result_discarded: bool = False


@dataclass(frozen=True)
class CharacterMemoryShadowInput:
    document_id: str
    chunk_index: int
    source_language: str
    target_language: str
    character_ids: tuple[str, ...]
    snapshot_id: str
    schema_version: str
    store_fingerprint: str
    scope: Mapping[str, str]
    token_budget: int
    created_at: str
    records: tuple[object, ...]
    conflicts: tuple[object, ...]


@dataclass(frozen=True)
class CharacterMemoryShadowResult:
    module: str
    status: str
    snapshot_id: str
    store_fingerprint: str
    selected_memory_ids: tuple[str, ...]
    selected_fact_types: tuple[str, ...]
    selected_character_ids: tuple[str, ...]
    selected_fingerprint: str
    estimated_tokens: int
    token_budget: int
    available_count: int
    eligible_count: int
    selected_count: int
    dropped_count: int
    drop_reasons: Mapping[str, int]
    dedup_savings: int
    conflict_count: int
    unresolved_identity_count: int
    expired_count: int
    inference_excluded_count: int
    human_approved_count: int
    memory_injected: bool = False
    prompt_identity_changed: bool = False
    production_output_changed: bool = False
    cache_identity_impact_planned: bool = False
    cache_identity_applied: bool = False
    duration_ms: float = 0.0
    result_discarded: bool = False


@dataclass(frozen=True)
class ContextSceneShadowInput:
    document_id: str
    chunk_index: int
    source_language: str
    target_language: str
    chapter_id: str
    scene_id: str
    sequence_index: int
    character_ids: tuple[str, ...]
    snapshot_id: str
    schema_version: str
    store_fingerprint: str
    scope: Mapping[str, str]
    token_budget: int
    previous_translation_allowed: bool
    expected_previous_translation_hash: str
    profile_id: str
    profile_version: str
    character_memory_selection_fingerprint: str
    created_at: str
    records: tuple[object, ...]
    scenes: tuple[object, ...]
    conflicts: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class ContextSceneShadowResult:
    module: str
    status: str
    snapshot_id: str
    store_fingerprint: str
    chapter_id: str
    scene_id: str
    scene_version: int
    participant_counts: Mapping[str, int]
    present_character_ids: tuple[str, ...]
    mentioned_character_ids: tuple[str, ...]
    exited_character_ids: tuple[str, ...]
    active_speaker_status: str
    point_of_view_status: str
    location_state_present: bool
    time_state_present: bool
    unresolved_reference_count: int
    unresolved_reference_evidence: tuple[Mapping[str, object], ...]
    selected_context_ids: tuple[str, ...]
    selected_context_types: tuple[str, ...]
    selected_fingerprint: str
    combined_context_fingerprint: str
    estimated_tokens: int
    budget: int
    available_records: int
    eligible_records: int
    selected_records: int
    dropped_records: int
    drop_reasons: Mapping[str, int]
    duplicate_savings: int
    stale_excluded: int
    expired_excluded: int
    conflict_excluded: int
    inference_excluded: int
    previous_translation_candidate: bool
    previous_translation_selected: bool
    previous_translation_injected: bool = False
    context_injected: bool = False
    scene_state_applied: bool = False
    prompt_modified: bool = False
    production_output_changed: bool = False
    cache_identity_impact_planned: bool = False
    cache_identity_applied: bool = False
    cache_hit_applied: bool = False
    provider_skipped: bool = False
    result_discarded: bool = False
    duration_ms: float = 0.0


@dataclass(frozen=True)
class ExtendedShadowGate:
    status: str
    requirements: Mapping[str, bool]
    reasons: tuple[str, ...]
    active_production_authorized: bool = False
