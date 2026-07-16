from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class ProviderCapability:
    supports_streaming: bool
    supports_json_mode: bool
    supports_dual_pass: bool
    supports_selective_polish: bool


@dataclass(frozen=True)
class ProviderQualityContract:
    contract_id: str
    version: str
    source_fidelity_required: bool
    no_omission: bool
    no_addition: bool
    no_summary: bool
    subject_reference_preservation: bool
    pronoun_reference_preservation: bool
    name_completion_forbidden: bool
    ambiguity_preservation: bool
    dialogue_quote_policy: str
    target_script_policy: str
    era_context_policy: str
    glossary_policy: str
    semantic_verification_required: bool


@dataclass(frozen=True)
class ProviderProfile:
    provider_id: str
    profile_version: str
    model_id: str
    provider_family: str
    supported_source_languages: tuple[str, ...]
    supported_target_languages: tuple[str, ...]
    context_limit: int
    output_limit: int
    supports_streaming: bool
    supports_json_mode: bool
    expected_timeout_seconds: int
    quality_contract_id: str
    quality_contract_version: str
    prompt_contract_id: str
    prompt_contract_version: str
    status: str
    fingerprint: str


@dataclass(frozen=True)
class ProviderFailureEvidence:
    evidence_id: str
    provider_id: str
    model_id: str
    failure_type: str
    prompt_identity: str
    occurrence_count: int
    timeout_seconds: int | None
    historical_evidence: bool
    current_health_unknown: bool
    created_at: str


@dataclass(frozen=True)
class ProviderAttemptRecord:
    provider_id: str
    model_id: str
    attempt_number: int
    failure_type: str | None
    input_tokens: int
    output_tokens: int
    elapsed_seconds: int


@dataclass(frozen=True)
class ProviderRoutingPolicy:
    policy_id: str
    version: str
    primary_provider_id: str
    fallback_provider_ids: tuple[str, ...]
    maximum_attempts_per_provider: int
    maximum_attempts_per_chunk: int
    maximum_total_requests_per_chunk: int
    retryable_failure_types: tuple[str, ...]
    non_retryable_failure_types: tuple[str, ...]
    backoff_policy: str
    timeout_increment_policy: str
    same_provider_retry_limit: int
    cross_provider_requires_manual_approval: bool
    academic_degraded_fallback: str


@dataclass(frozen=True)
class ProviderRequestBudget:
    maximum_requests_per_chunk: int
    maximum_requests_per_document: int
    maximum_retry_requests: int
    maximum_fallback_requests: int
    maximum_polish_requests: int
    maximum_total_input_tokens: int
    maximum_total_output_tokens: int
    maximum_wall_clock_seconds: int


@dataclass(frozen=True)
class ProviderTimeoutBudget:
    per_attempt_timeout_seconds: int
    maximum_chunk_wall_clock_seconds: int
    maximum_document_timeout_events: int
    provider_timeout_history: tuple[Mapping[str, Any], ...]
    timeout_risk_level: str


@dataclass(frozen=True)
class ProviderRoutingInput:
    document_id: str
    chunk_index: int
    source_language: str
    target_language: str
    language_profile_id: str
    language_profile_version: str
    language_profile_fingerprint: str
    prompt_identity: str
    context_identity: str
    glossary_identity: str
    quality_policy_identity: str
    semantic_policy_identity: str
    semantic_verification_available: bool
    translation_mode: str
    draft_required: bool
    polish_required: bool
    estimated_input_tokens: int
    estimated_output_tokens: int
    chunk_length: int
    provider_health_evidence: Mapping[str, str]
    provider_failure_history: tuple[ProviderFailureEvidence, ...]
    cache_availability: bool
    verified_draft_available: bool
    request_budget: ProviderRequestBudget
    timeout_budget: ProviderTimeoutBudget
    current_requests: int
    current_document_requests: int
    current_retry_requests: int
    current_fallback_requests: int
    current_polish_requests: int
    current_input_tokens: int
    current_output_tokens: int
    current_wall_clock_seconds: int
    manual_approval_granted: bool
    created_at: str


@dataclass(frozen=True)
class ProviderCompatibilityResult:
    status: str
    compatible: bool
    reasons: tuple[str, ...]
    manual_review_required: bool
    quality_contract_compatible: bool
    prompt_contract_compatible: bool


@dataclass(frozen=True)
class ProviderRetryDecision:
    status: str
    retry_allowed: bool
    reasons: tuple[str, ...]
    planned_requests: int
    manual_approval_required: bool


@dataclass(frozen=True)
class ProviderFallbackDecision:
    status: str
    fallback_allowed: bool
    fallback_provider_id: str | None
    reasons: tuple[str, ...]
    manual_approval_required: bool


@dataclass(frozen=True)
class ProviderRoutingDecision:
    selected_provider: str | None
    selected_model: str | None
    decision: str
    reasons: tuple[str, ...]
    eligible_providers: tuple[str, ...]
    ineligible_providers: tuple[str, ...]
    retry_allowed: bool
    fallback_allowed: bool
    estimated_requests: int
    maximum_requests: int
    estimated_timeout_risk: str
    cache_reuse_recommended: bool
    verified_draft_reuse_recommended: bool
    manual_approval_required: bool


@dataclass(frozen=True)
class ProviderExecutionPlan:
    prepare_only: bool
    executed: bool
    network_requests: int
    selected_provider: str | None
    selected_model: str | None
    attempts: tuple[Mapping[str, Any], ...]
    fallback_sequence: tuple[str, ...]
    maximum_requests: int
    timeout_per_attempt: int
    maximum_wall_clock: int
    required_cache_identity: str
    required_quality_policy: str
    required_semantic_policy: str
    manual_approval_required: bool
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ProviderRoutingEvidence:
    routing_decision_id: str
    input_fingerprint: str
    policy_version: str
    eligible_providers: tuple[str, ...]
    selected_provider: str | None
    rejected_providers: tuple[str, ...]
    failure_evidence_used: tuple[str, ...]
    budget_evidence: Mapping[str, Any]
    compatibility_evidence: Mapping[str, Any]
    decision: str
    reasons: tuple[str, ...]
    created_at: str
