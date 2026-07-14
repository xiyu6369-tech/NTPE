from __future__ import annotations

import json
from pathlib import Path

from .integrity import review_artifact_sha256
from .redaction import assert_review_redacted


def verify_review_artifact(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("integrity", {})
    if integrity.get("payload_sha256") != review_artifact_sha256(payload):
        raise ValueError("structured review artifact integrity failure")
    assert_review_redacted(payload)
    if payload.get("content_redacted") is not True:
        raise ValueError("structured review artifact is not redacted")
    return payload
