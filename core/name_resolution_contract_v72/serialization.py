from __future__ import annotations

import hashlib
import json


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def deterministic_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()
