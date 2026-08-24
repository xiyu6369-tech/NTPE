from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from core.adaptive_context_authorized_provider_harness import CREDENTIAL_ENV
from core.adaptive_context_provider_execution_freeze import verify_freeze_artifact
from core.adaptive_context_real_provider_boundary import (
    ALLOWED_CREDENTIAL_ENV,
    ALLOWED_MODELS,
    ALLOWED_PROVIDER_URLS,
)
from core.production_runtime.manifest import (
    get_te_v7_stage_path,
    get_te_v7_artifact_path,
    TE_V7_STAGE108_FAKE_TRANSPORT_FREEZE,
    TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT,
)

from .config import (
    MAX_PREFLIGHT_ATTEMPTS,
    RealProviderPreflightConfig,
    safe_identifier,
    sha256_shape,
)
from .model import PreflightChecks


def resolve_preflight_artifact_path(path: str | Path, *, root: str | Path) -> Path:
    base = Path(root).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    target = target.resolve()
    if target.suffix.lower() != ".json":
        raise ValueError("real-provider-preflight-artifact-extension-invalid")
    allowed = (
        get_te_v7_stage_path(base, "te_v7_stage109"),
        (base / ".ntpe_test_sandbox").resolve(),
    )
    if not any(target == directory or directory in target.parents for directory in allowed):
        raise ValueError("real-provider-preflight-artifact-path-forbidden")
    stage09 = get_te_v7_stage_path(base, "te_v7_stage09")
    if target == stage09 or stage09 in target.parents:
        raise ValueError("real-provider-preflight-stage09-overwrite-forbidden")
    return target


def _credential_available(environ: Mapping[str, str]) -> bool:
    # Convert directly to a boolean. No credential-derived property survives.
    return CREDENTIAL_ENV in environ and bool(environ[CREDENTIAL_ENV])


def _attempt_plan_checks(config: RealProviderPreflightConfig) -> tuple[bool, bool, bool]:
    plans = config.attempt_plan
    retry_bound = (
        0 <= config.max_retries < MAX_PREFLIGHT_ATTEMPTS
        and bool(plans)
        and len(plans) <= MAX_PREFLIGHT_ATTEMPTS
        and len(plans) - 1 <= config.max_retries
    )
    timeouts = bool(plans) and all(plan.timeout_seconds > 0 for plan in plans)
    plan_valid = (
        retry_bound
        and timeouts
        and [plan.attempt for plan in plans] == list(range(1, len(plans) + 1))
        and all(plan.valid() for plan in plans)
        and all((plan.attempt == 1) != plan.fallback_used for plan in plans)
    )
    return plan_valid, retry_bound, timeouts


def _stage108_integrity_valid(config: RealProviderPreflightConfig, root: Path) -> bool:
    expected = get_te_v7_artifact_path(root, "te_v7_stage108", TE_V7_STAGE108_FAKE_TRANSPORT_FREEZE)
    candidate = Path(config.stage108_freeze_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        if candidate.resolve() != expected:
            return False
        frozen = verify_freeze_artifact(candidate)
        return (
            frozen.network_requests == 0
            and not frozen.real_provider_executed
            and frozen.stage09_artifacts_unchanged
            and frozen.te_v6_frozen_runtime_unchanged
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def _te_v6_invariants_valid(config: RealProviderPreflightConfig, root: Path) -> bool:
    expected = (root / "manifests/te_v600_final_release_manifest.json").resolve()
    candidate = Path(config.te_v6_manifest_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        if candidate.resolve() != expected:
            return False
        manifest = json.loads(candidate.read_text(encoding="utf-8"))
        if manifest.get("version") != "6.0.0" or manifest.get("frozen") is not True:
            return False
        if not {"08.1", "10.1.1", "11.6", "12.5"}.issubset(manifest.get("frozen_stages", ())):
            return False
        if "meta/llama-3.3-70b-instruct" not in manifest.get("provider_invariants", ()):
            return False
        for row in manifest.get("file_inventory", ()):
            path = root / row["path"]
            if not path.is_file():
                return False
            if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                return False
        return True
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _production_launcher_unconnected(root: Path) -> bool:
    try:
        source = (root / "ntpe_authorized_provider_invocation.py").read_text(encoding="utf-8")
    except OSError:
        return False
    return all(marker not in source for marker in (
        "launcher_translate", "ntpe_production_translate", "translation_runtime",
    ))


def collect_preflight_checks(
    config: RealProviderPreflightConfig, *, root: str | Path,
    environ: Mapping[str, str],
) -> PreflightChecks:
    base = Path(root).resolve()
    plan_valid, retry_bound, timeout_valid = _attempt_plan_checks(config)
    try:
        resolve_preflight_artifact_path(config.artifact_path, root=base)
        artifact_path_valid = True
    except (OSError, ValueError):
        artifact_path_valid = False
    return PreflightChecks(
        boundary_enabled=config.boundary_enabled,
        real_provider_enabled=config.real_provider_enabled,
        authorization_recorded=bool(config.authorization_id.strip()),
        authorization_format_valid=safe_identifier(config.authorization_id),
        credential_available=_credential_available(environ),
        endpoint_allowlisted=(
            config.provider_url in ALLOWED_PROVIDER_URLS
            and ALLOWED_CREDENTIAL_ENV.get(config.provider) == CREDENTIAL_ENV
        ),
        model_allowlisted=config.model in ALLOWED_MODELS,
        fallback_models_allowlisted=all(model in ALLOWED_MODELS for model in config.fallback_models),
        single_chunk=config.single_chunk_only and config.chunk_count == 1,
        single_session=config.single_controlled_session,
        attempt_plan_valid=plan_valid,
        retry_bound_valid=retry_bound,
        timeout_valid=timeout_valid,
        source_identity_valid=safe_identifier(config.source_identity),
        source_fingerprint_valid=sha256_shape(config.source_fingerprint),
        resume_excluded=not config.resumed,
        artifact_path_valid=artifact_path_valid,
        stage108_integrity_valid=_stage108_integrity_valid(config, base),
        te_v6_invariants_valid=_te_v6_invariants_valid(config, base),
        production_launcher_unconnected=_production_launcher_unconnected(base),
    )
