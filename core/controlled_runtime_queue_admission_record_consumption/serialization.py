from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from typing import Any


def _n(v: Any) -> Any:
    if isinstance(v, str):
        return v.replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(v, (tuple, list)):
        return [_n(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _n(x) for k, x in v.items()}
    if is_dataclass(v):
        return {f.name: _n(getattr(v, f.name)) for f in fields(v)}
    return v


def canonical_json(v: Any) -> str:
    return json.dumps(
        _n(v), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def canonical_sha256(v: Any) -> str:
    return hashlib.sha256(canonical_json(v).encode()).hexdigest()


def values(v: Any, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
    return {f.name: _n(getattr(v, f.name)) for f in fields(v) if f.name not in exclude}