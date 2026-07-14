from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from core.adaptive_context_provider_evidence.redaction import assert_redacted
from core.adaptive_context_provider_evidence_pipeline import artifact_sha256

from .freeze import FakeTransportFreezeArtifact


def _resolve_freeze_path(path: str | Path, *, root: str | Path) -> Path:
    base = Path(root).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    target = target.resolve()
    allowed = (
        (base / "artifacts" / "te_v7_stage108").resolve(),
        (base / ".ntpe_test_sandbox").resolve(),
    )
    if not any(target == directory or directory in target.parents for directory in allowed):
        raise ValueError("provider-execution-freeze-artifact-path-forbidden")
    stage09 = (base / "artifacts" / "te_v7_stage09").resolve()
    if target == stage09 or stage09 in target.parents:
        raise ValueError("provider-execution-freeze-stage09-overwrite-forbidden")
    return target


def write_freeze_artifact(
    artifact: FakeTransportFreezeArtifact, path: str | Path, *, root: str | Path,
) -> Path:
    payload = asdict(artifact)
    if artifact.status != "fake_transport_end_to_end_frozen":
        raise ValueError("provider execution freeze artifact is not frozen")
    assert_redacted(payload)
    payload["integrity"] = {"algorithm": "sha256", "payload_sha256": artifact_sha256(payload)}
    target = _resolve_freeze_path(path, root=root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def verify_freeze_artifact(path: str | Path) -> FakeTransportFreezeArtifact:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("integrity", {})
    if integrity.get("payload_sha256") != artifact_sha256(payload):
        raise ValueError("provider execution freeze artifact integrity failure")
    assert_redacted(payload)
    artifact = FakeTransportFreezeArtifact(**payload)
    if artifact.status != "fake_transport_end_to_end_frozen":
        raise ValueError("provider execution freeze artifact status invalid")
    if any((
        artifact.network_requests != 0,
        artifact.real_provider_executed,
        artifact.readiness_evaluated,
        artifact.comparison_executed,
        not artifact.content_redacted,
        artifact.production_launcher_connected,
        artifact.provider_benchmark_complete,
    )):
        raise ValueError("provider execution freeze artifact boundary failure")
    return artifact
