from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .config import RealProviderPreflightConfig
from .model import (
    PREFLIGHT_STATUSES,
    PreflightChecks,
    RealProviderPreflightArtifact,
    RealProviderPreflightResult,
)
from .validator import collect_preflight_checks


def _status(config: RealProviderPreflightConfig, checks: PreflightChecks) -> str:
    if not config.enabled:
        return "disabled"
    if not checks.boundary_enabled:
        return "blocked_missing_boundary_enable"
    if not checks.real_provider_enabled:
        return "blocked_missing_real_provider_enable"
    if not checks.authorization_recorded:
        return "blocked_missing_authorization"
    if not checks.authorization_format_valid:
        return "blocked_invalid_authorization"
    if not checks.credential_available:
        return "blocked_missing_credential"
    if not checks.endpoint_allowlisted:
        return "blocked_invalid_endpoint"
    if not checks.model_allowlisted or not checks.fallback_models_allowlisted:
        return "blocked_invalid_model"
    if not all((
        checks.single_chunk,
        checks.single_session,
        checks.attempt_plan_valid,
        checks.retry_bound_valid,
        checks.timeout_valid,
    )):
        return "blocked_invalid_attempt_plan"
    if not checks.source_identity_valid:
        return "blocked_invalid_source_identity"
    if not checks.source_fingerprint_valid:
        return "blocked_invalid_source_fingerprint"
    if not checks.resume_excluded:
        return "blocked_resume_chunk"
    if not checks.artifact_path_valid:
        return "blocked_artifact_path"
    if not checks.stage108_integrity_valid:
        return "blocked_freeze_integrity"
    if not checks.te_v6_invariants_valid:
        return "blocked_frozen_invariants"
    if not checks.production_launcher_unconnected:
        return "blocked_production_connection"
    return "eligible_for_explicit_real_provider_authorization"


def evaluate_real_provider_preflight(
    config: RealProviderPreflightConfig, *, root: str | Path,
    environ: Mapping[str, str],
) -> RealProviderPreflightResult:
    checks = collect_preflight_checks(config, root=root, environ=environ)
    status = _status(config, checks)
    if status not in PREFLIGHT_STATUSES:
        raise ValueError("real-provider-preflight-status-invalid")
    eligible = status == "eligible_for_explicit_real_provider_authorization"
    blockers = () if eligible else (status,)
    artifact = RealProviderPreflightArtifact(
        stage="TE-v7.0-Stage10.9",
        status=status,
        eligible=eligible,
        boundary_enabled=checks.boundary_enabled,
        real_provider_enabled=checks.real_provider_enabled,
        authorization_recorded=(
            checks.authorization_recorded and checks.authorization_format_valid
        ),
        credential_available=checks.credential_available,
        endpoint_allowlisted=checks.endpoint_allowlisted,
        model_allowlisted=(checks.model_allowlisted and checks.fallback_models_allowlisted),
        single_chunk=checks.single_chunk,
        single_session=checks.single_session,
        attempt_plan_valid=(
            checks.attempt_plan_valid and checks.retry_bound_valid and checks.timeout_valid
        ),
        resume_excluded=checks.resume_excluded,
        artifact_path_valid=checks.artifact_path_valid,
        stage108_integrity_valid=checks.stage108_integrity_valid,
        te_v6_invariants_valid=checks.te_v6_invariants_valid,
        production_launcher_unconnected=checks.production_launcher_unconnected,
    )
    return RealProviderPreflightResult(artifact=artifact, blockers=blockers)
