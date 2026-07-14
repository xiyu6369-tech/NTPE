from __future__ import annotations

import json
from pathlib import Path

from core.adaptive_context_provider_evidence.redaction import assert_redacted

from .integrity import preflight_sha256
from .model import PREFLIGHT_STATUSES, RealProviderPreflightArtifact
from .validator import resolve_preflight_artifact_path


def _validate_artifact(artifact: RealProviderPreflightArtifact) -> None:
    eligible_status = "eligible_for_explicit_real_provider_authorization"
    if artifact.status not in PREFLIGHT_STATUSES:
        raise ValueError("real-provider-preflight-artifact-status-invalid")
    if artifact.eligible != (artifact.status == eligible_status):
        raise ValueError("real-provider-preflight-artifact-eligibility-invalid")
    if artifact.eligible and not all((
        artifact.boundary_enabled,
        artifact.real_provider_enabled,
        artifact.authorization_recorded,
        artifact.credential_available,
        artifact.endpoint_allowlisted,
        artifact.model_allowlisted,
        artifact.single_chunk,
        artifact.single_session,
        artifact.attempt_plan_valid,
        artifact.resume_excluded,
        artifact.artifact_path_valid,
        artifact.stage108_integrity_valid,
        artifact.te_v6_invariants_valid,
        artifact.production_launcher_unconnected,
    )):
        raise ValueError("real-provider-preflight-artifact-admission-invalid")
    if any((
        artifact.network_requests != 0,
        artifact.provider_executed,
        artifact.translation_output_generated,
        artifact.baseline_created,
        artifact.candidate_created,
        artifact.comparison_executed,
        artifact.readiness_evaluated,
        not artifact.content_redacted,
    )):
        raise ValueError("real-provider-preflight-artifact-boundary-invalid")


def write_preflight_artifact(
    artifact: RealProviderPreflightArtifact, path: str | Path, *, root: str | Path,
) -> Path:
    _validate_artifact(artifact)
    payload = artifact.to_dict()
    assert_redacted(payload)
    payload["integrity"] = {
        "algorithm": "sha256", "payload_sha256": preflight_sha256(payload),
    }
    target = resolve_preflight_artifact_path(path, root=root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def verify_preflight_artifact(path: str | Path) -> RealProviderPreflightArtifact:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("integrity", {})
    if integrity.get("payload_sha256") != preflight_sha256(payload):
        raise ValueError("real Provider preflight artifact integrity failure")
    assert_redacted(payload)
    artifact = RealProviderPreflightArtifact(**payload)
    _validate_artifact(artifact)
    return artifact
