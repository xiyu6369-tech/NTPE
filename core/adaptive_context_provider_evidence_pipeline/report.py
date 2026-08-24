from __future__ import annotations

import json
from pathlib import Path

from core.adaptive_context_provider_evidence.redaction import assert_redacted
from core.production_runtime.manifest import get_te_v7_stage_path

from .integrity import artifact_sha256
from .model import ProviderEvidenceArtifact, ProviderEvidenceAttempt
from .validator import validate_provider_evidence_artifact


def _resolve_report_path(path: str | Path, *, root: str | Path) -> Path:
    base = Path(root).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    target = target.resolve()
    allowed = tuple(
        get_te_v7_stage_path(base, stage) for stage in (
            "te_v7_stage10",
            "te_v7_stage107",
            "te_v7_stage108",
        )
    ) + ((base / ".ntpe_test_sandbox").resolve(),)
    if not any(target == directory or directory in target.parents for directory in allowed):
        raise ValueError("provider-evidence-artifact-path-outside-stage10-sandbox")
    stage09 = get_te_v7_stage_path(base, "te_v7_stage09")
    if target == stage09 or stage09 in target.parents:
        raise ValueError("provider-evidence-stage09-overwrite-forbidden")
    return target


def write_provider_evidence_artifact(
    artifact: ProviderEvidenceArtifact, path: str | Path, *, root: str | Path,
) -> Path:
    blockers = validate_provider_evidence_artifact(artifact)
    if blockers:
        raise ValueError(",".join(blockers))
    payload = artifact.to_dict()
    assert_redacted(payload)
    payload["integrity"] = {"algorithm": "sha256", "payload_sha256": artifact_sha256(payload)}
    target = _resolve_report_path(path, root=root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def verify_provider_evidence_artifact(path: str | Path) -> ProviderEvidenceArtifact:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("integrity", {})
    if integrity.get("payload_sha256") != artifact_sha256(payload):
        raise ValueError("provider evidence artifact rejected_integrity")
    assert_redacted(payload)
    payload["attempts"] = tuple(ProviderEvidenceAttempt(**row) for row in payload["attempts"])
    payload["limitations"] = tuple(payload.get("limitations", ()))
    artifact = ProviderEvidenceArtifact(**payload)
    blockers = validate_provider_evidence_artifact(artifact)
    if blockers:
        raise ValueError(",".join(blockers))
    return artifact
