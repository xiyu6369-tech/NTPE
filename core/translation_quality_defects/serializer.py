from __future__ import annotations

import json
from pathlib import Path

from .integrity import quality_defects_sha256


def verify_defect_artifact(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("integrity", {})
    if integrity.get("payload_sha256") != quality_defects_sha256(payload):
        raise ValueError("translation defect artifact integrity failure")
    if payload.get("human_review_based") is not True or payload.get("new_translation_generated") is not False:
        raise ValueError("translation defect artifact boundary invalid")
    return payload
