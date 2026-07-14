from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .config import PREFLIGHT_VERSION

PREFLIGHT_STATUSES = frozenset({
    "disabled",
    "blocked_missing_boundary_enable",
    "blocked_missing_real_provider_enable",
    "blocked_missing_authorization",
    "blocked_invalid_authorization",
    "blocked_missing_credential",
    "blocked_invalid_endpoint",
    "blocked_invalid_model",
    "blocked_invalid_attempt_plan",
    "blocked_invalid_source_identity",
    "blocked_invalid_source_fingerprint",
    "blocked_resume_chunk",
    "blocked_artifact_path",
    "blocked_freeze_integrity",
    "blocked_frozen_invariants",
    "blocked_production_connection",
    "eligible_for_explicit_real_provider_authorization",
})


@dataclass(frozen=True)
class PreflightChecks:
    boundary_enabled: bool
    real_provider_enabled: bool
    authorization_recorded: bool
    authorization_format_valid: bool
    credential_available: bool
    endpoint_allowlisted: bool
    model_allowlisted: bool
    fallback_models_allowlisted: bool
    single_chunk: bool
    single_session: bool
    attempt_plan_valid: bool
    retry_bound_valid: bool
    timeout_valid: bool
    source_identity_valid: bool
    source_fingerprint_valid: bool
    resume_excluded: bool
    artifact_path_valid: bool
    stage108_integrity_valid: bool
    te_v6_invariants_valid: bool
    production_launcher_unconnected: bool


@dataclass(frozen=True)
class RealProviderPreflightArtifact:
    stage: str
    status: str
    eligible: bool
    boundary_enabled: bool
    real_provider_enabled: bool
    authorization_recorded: bool
    credential_available: bool
    endpoint_allowlisted: bool
    model_allowlisted: bool
    single_chunk: bool
    single_session: bool
    attempt_plan_valid: bool
    resume_excluded: bool
    artifact_path_valid: bool
    stage108_integrity_valid: bool
    te_v6_invariants_valid: bool
    production_launcher_unconnected: bool
    network_requests: int = 0
    provider_executed: bool = False
    translation_output_generated: bool = False
    baseline_created: bool = False
    candidate_created: bool = False
    comparison_executed: bool = False
    readiness_evaluated: bool = False
    content_redacted: bool = True
    version: str = PREFLIGHT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RealProviderPreflightResult:
    artifact: RealProviderPreflightArtifact
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "blockers", tuple(self.blockers))
