from __future__ import annotations

import json
from pathlib import Path

from core.adaptive_context_provider_evidence.redaction import assert_redacted
from core.adaptive_context_provider_evidence_pipeline import ProviderEvidenceAttempt

from .integrity import controlled_retry_sha256
from .model import CONTROLLED_RETRY_STATUSES, ControlledRetryArtifact
from .token_evidence import ControlledRetryTokenEvidence


def resolve_controlled_retry_artifact_path(
    path: str | Path, *, root: str | Path,
) -> Path:
    base = Path(root).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    target = target.resolve()
    if target.suffix.lower() != ".json":
        raise ValueError("controlled-retry-artifact-extension-invalid")
    allowed = (
        (base / "artifacts" / "te_v7_stage10101").resolve(),
        (base / ".ntpe_test_sandbox").resolve(),
    )
    if not any(target == directory or directory in target.parents for directory in allowed):
        raise ValueError("controlled-retry-artifact-path-forbidden")
    return target


def resolve_controlled_retry_review_path(
    path: str | Path, *, root: str | Path,
) -> Path:
    base = Path(root).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    target = target.resolve()
    if target.suffix.lower() != ".txt":
        raise ValueError("controlled-retry-review-extension-invalid")
    allowed = (
        (base / "artifacts" / "te_v7_stage10101" / "review").resolve(),
        (base / ".ntpe_test_sandbox").resolve(),
    )
    if not any(target == directory or directory in target.parents for directory in allowed):
        raise ValueError("controlled-retry-review-path-forbidden")
    return target


def _validate(artifact: ControlledRetryArtifact) -> None:
    if artifact.status not in CONTROLLED_RETRY_STATUSES:
        raise ValueError("controlled-retry-artifact-status-invalid")
    if any((
        artifact.timeout_seconds != 180,
        artifact.attempt_limit != 1,
        artifact.fallback_allowed,
        artifact.comparison_executed,
        artifact.readiness_evaluated,
        artifact.baseline_created,
        artifact.candidate_created,
        artifact.production_ready,
        not artifact.human_review_required,
        not artifact.content_redacted,
    )):
        raise ValueError("controlled-retry-artifact-boundary-invalid")
    if artifact.status == "controlled_retry_contract_prepared" and any((
        artifact.real_provider_execution,
        artifact.network_requests,
        artifact.retry_executed,
        artifact.translation_output_generated,
    )):
        raise ValueError("controlled-retry-prepared-claim-invalid")


def write_controlled_retry_artifact(
    artifact: ControlledRetryArtifact, path: str | Path, *, root: str | Path,
) -> Path:
    _validate(artifact)
    payload = artifact.to_dict()
    assert_redacted(payload)
    payload["integrity"] = {
        "algorithm": "sha256",
        "payload_sha256": controlled_retry_sha256(payload),
    }
    target = resolve_controlled_retry_artifact_path(path, root=root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def verify_controlled_retry_artifact(path: str | Path) -> ControlledRetryArtifact:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("integrity", {})
    if integrity.get("payload_sha256") != controlled_retry_sha256(payload):
        raise ValueError("controlled retry artifact integrity failure")
    assert_redacted(payload)
    payload["attempts"] = tuple(ProviderEvidenceAttempt(**row) for row in payload["attempts"])
    payload["token_evidence"] = ControlledRetryTokenEvidence(**payload["token_evidence"])
    artifact = ControlledRetryArtifact(**payload)
    _validate(artifact)
    return artifact


def write_controlled_retry_review(
    text: str, path: str | Path, *, root: str | Path,
) -> Path:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("controlled-retry-review-output-empty")
    target = resolve_controlled_retry_review_path(path, root=root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.strip() + "\n", encoding="utf-8")
    return target
