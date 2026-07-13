from __future__ import annotations

import hashlib
import json
from typing import Mapping


def payload_fingerprint(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def report_sha256(payload: Mapping[str, object]) -> str:
    clean = {key: value for key, value in payload.items() if key != "artifact_sha256"}
    encoded = json.dumps(clean, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
