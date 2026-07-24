"""Internal canonical serialization helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from typing import Any


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if is_dataclass(value):
        return {
            item.name: _normalize(getattr(value, item.name))
            for item in fields(value)
        }
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        _normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def model_values(value: Any, *, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        item.name: _normalize(getattr(value, item.name))
        for item in fields(value)
        if item.name not in exclude
    }
