from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"
MODULE_VERSION = "lcr-batch10-shadow-1.0"


@dataclass(frozen=True)
class ProductionShadowInput:
    document_id: str
    chunk_index: int
    source_hash: str
    source_language: str
    target_language: str
    prompt_identity: str
    provider_identity: str
    model_identity: str
    quality_policy_identity: str
    resume_identity: str
    output_contract_identity: str
    baseline_context_fingerprint: str
    baseline_glossary_fingerprint: str
    runtime_version: str
    feature_flag_state: Mapping[str, bool]
    created_at: str


@dataclass(frozen=True)
class ProductionShadowResult:
    shadow_id: str
    input_fingerprint: str
    modules_evaluated: tuple[str, ...]
    character_memory_view: Mapping[str, Any]
    context_scene_view: Mapping[str, Any]
    cache_decision: Mapping[str, Any]
    dual_pass_decision: Mapping[str, Any]
    semantic_verification_requirement: bool
    language_profile_view: Mapping[str, Any]
    provider_route_view: Mapping[str, Any]
    readiness_result: str
    baseline_changed: bool = False
    production_output_changed: bool = False
    provider_requests_planned: int = 0
    provider_requests_executed: int = 0
    warnings: tuple[str, ...] = ()
    blocking_reasons: tuple[str, ...] = ()
    deterministic_fingerprint: str = ""


@dataclass(frozen=True)
class BaselineShadowComparison:
    prompt_identity: Mapping[str, Any]
    provider_identity: Mapping[str, Any]
    language_profile_identity: Mapping[str, Any]
    context_fingerprint: Mapping[str, Any]
    glossary_fingerprint: Mapping[str, Any]
    cache_eligibility: Mapping[str, Any]
    retry_plan: Mapping[str, Any]
    output_contract: Mapping[str, Any]
    quality_requirement: Mapping[str, Any]
    planned_request_count: Mapping[str, Any]
    warnings: tuple[str, ...] = ()
    blocking_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActivationGateResult:
    status: str
    requirements: Mapping[str, bool]
    reasons: tuple[str, ...]
    active_production_authorized: bool = False


@dataclass(frozen=True)
class RollbackStep:
    level: int
    trigger: str
    action: str
    expected_result: str
    data_preserved: tuple[str, ...]
    production_impact: str
    verification: str


def to_mapping(value: Any) -> Mapping[str, Any]:
    return asdict(value)
