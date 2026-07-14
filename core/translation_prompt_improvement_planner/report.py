from __future__ import annotations

import json
from pathlib import Path

from .integrity import improvement_plan_sha256


def verify_improvement_plan_artifact(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("integrity", {})
    if integrity.get("payload_sha256") != improvement_plan_sha256(payload):
        raise ValueError("prompt improvement plan artifact integrity failure")
    boundaries = ("prompt_modified", "runtime_modified", "provider_executed", "new_translation_generated")
    if any(payload.get(field) is not False for field in boundaries) or payload.get("plans_applied") != 0 or payload.get("human_approval_required") is not True:
        raise ValueError("prompt improvement plan boundary invalid")
    return payload
