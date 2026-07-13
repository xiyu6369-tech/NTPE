from __future__ import annotations

import hashlib
import json
from typing import Mapping


def canonical_bytes(payload: Mapping[str, object]) -> bytes:
    clean = {key: value for key, value in payload.items() if key != "artifact_sha256"}
    return json.dumps(clean, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def payload_sha256(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()
