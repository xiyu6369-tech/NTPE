from __future__ import annotations

import json
from pathlib import Path

from .integrity import payload_sha256
from .model import ProviderEvidenceBundle, ProviderRequestIdentity, ProviderTimingEvidence, TokenUsageEvidence
from .redaction import assert_redacted


def write_provider_evidence(bundle: ProviderEvidenceBundle, path: str | Path) -> Path:
    payload = bundle.to_dict()
    payload["content_redacted"] = True
    assert_redacted(payload)
    payload["artifact_sha256"] = {"algorithm": "sha256", "payload_sha256": payload_sha256(payload)}
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def load_provider_evidence(path: str | Path) -> ProviderEvidenceBundle:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("artifact_sha256", {})
    if integrity.get("payload_sha256") != payload_sha256(payload):
        raise ValueError("provider evidence artifact integrity failure")
    assert_redacted(payload)
    records = []
    for raw in payload.pop("request_evidence", ()):
        raw["token_usage"] = TokenUsageEvidence(**raw.get("token_usage", {}))
        raw.pop("version", None)
        records.append(ProviderTimingEvidence(**raw))
    payload.pop("version", None)
    return ProviderEvidenceBundle(records=tuple(records), **payload)
