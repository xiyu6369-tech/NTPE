from __future__ import annotations

import json
from pathlib import Path

from .integrity import quality_metrics_sha256


def verify_quality_metrics_artifact(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("integrity", {})
    if integrity.get("payload_sha256") != quality_metrics_sha256(payload):
        raise ValueError("quality metrics artifact integrity failure")
    if payload.get("provider_execution_performed") is not False or payload.get("new_translation_generated") is not False:
        raise ValueError("quality metrics artifact boundary invalid")
    return payload
