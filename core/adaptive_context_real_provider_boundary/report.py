from __future__ import annotations

import json
from pathlib import Path

from core.adaptive_context_provider_benchmark_session.integrity import report_sha256
from core.adaptive_context_provider_evidence.redaction import assert_redacted

from .model import BoundaryInvocationResult


def write_boundary_report(result: BoundaryInvocationResult, path: str | Path) -> Path:
    payload = result.to_dict()
    payload["content_redacted"] = True
    assert_redacted(payload)
    payload["artifact_sha256"] = {"algorithm": "sha256", "payload_sha256": report_sha256(payload)}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def verify_boundary_report(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("artifact_sha256", {})
    if integrity.get("payload_sha256") != report_sha256(payload):
        raise ValueError("real Provider boundary artifact integrity failure")
    assert_redacted(payload)
    return payload
