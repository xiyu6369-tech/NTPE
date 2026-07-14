from __future__ import annotations

import json
from pathlib import Path

from core.adaptive_context_provider_evidence.redaction import assert_redacted
from core.adaptive_context_provider_evidence_pipeline import ProviderEvidenceAttempt

from .integrity import invocation_sha256
from .model import INVOCATION_STATUSES, SingleRealInvocationArtifact


def resolve_invocation_artifact_path(path: str | Path, *, root: str | Path) -> Path:
    base = Path(root).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    target = target.resolve()
    if target.suffix.lower() != ".json":
        raise ValueError("single-real-invocation-artifact-extension-invalid")
    allowed = (
        (base / "artifacts" / "te_v7_stage1010").resolve(),
        (base / ".ntpe_test_sandbox").resolve(),
    )
    if not any(target == directory or directory in target.parents for directory in allowed):
        raise ValueError("single-real-invocation-artifact-path-forbidden")
    stage09 = (base / "artifacts" / "te_v7_stage09").resolve()
    if target == stage09 or stage09 in target.parents:
        raise ValueError("single-real-invocation-stage09-overwrite-forbidden")
    return target


def resolve_review_path(path: str | Path, *, root: str | Path) -> Path:
    base = Path(root).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    target = target.resolve()
    if target.suffix.lower() != ".txt":
        raise ValueError("single-real-invocation-review-extension-invalid")
    allowed = (
        (base / "artifacts" / "te_v7_stage1010" / "review").resolve(),
        (base / ".ntpe_test_sandbox").resolve(),
    )
    if not any(target == directory or directory in target.parents for directory in allowed):
        raise ValueError("single-real-invocation-review-path-forbidden")
    return target


def _validate_artifact(artifact: SingleRealInvocationArtifact) -> None:
    if artifact.status not in INVOCATION_STATUSES:
        raise ValueError("single-real-invocation-artifact-status-invalid")
    if any((
        artifact.comparison_executed,
        artifact.readiness_evaluated,
        artifact.baseline_created,
        artifact.candidate_created,
        artifact.production_ready,
        not artifact.human_review_required,
        not artifact.content_redacted,
    )):
        raise ValueError("single-real-invocation-artifact-boundary-invalid")
    if artifact.status == "stage1010a_fake_transport_validated" and any((
        artifact.real_provider_execution,
        artifact.network_requests != 0,
        artifact.translation_output_generated,
    )):
        raise ValueError("single-real-invocation-fake-artifact-claim-invalid")
    if artifact.real_provider_execution and artifact.network_requests < 1:
        raise ValueError("single-real-invocation-network-accounting-invalid")


def write_invocation_artifact(
    artifact: SingleRealInvocationArtifact, path: str | Path, *, root: str | Path,
) -> Path:
    _validate_artifact(artifact)
    payload = artifact.to_dict()
    assert_redacted(payload)
    payload["integrity"] = {
        "algorithm": "sha256", "payload_sha256": invocation_sha256(payload),
    }
    target = resolve_invocation_artifact_path(path, root=root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def verify_invocation_artifact(path: str | Path) -> SingleRealInvocationArtifact:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("integrity", {})
    if integrity.get("payload_sha256") != invocation_sha256(payload):
        raise ValueError("single real invocation artifact integrity failure")
    assert_redacted(payload)
    payload["attempts"] = tuple(ProviderEvidenceAttempt(**row) for row in payload["attempts"])
    artifact = SingleRealInvocationArtifact(**payload)
    _validate_artifact(artifact)
    return artifact


def write_translation_review(text: str, path: str | Path, *, root: str | Path) -> Path:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("single-real-invocation-review-output-empty")
    target = resolve_review_path(path, root=root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.strip() + "\n", encoding="utf-8")
    return target
