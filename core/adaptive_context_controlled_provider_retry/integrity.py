from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping


def controlled_retry_sha256(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
