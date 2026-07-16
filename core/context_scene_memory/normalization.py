from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Iterable


def normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("text must be a string")
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()


def canonical_hash(parts: Iterable[object]) -> str:
    payload = json.dumps(list(parts), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_{canonical_hash(parts)[:24]}"

