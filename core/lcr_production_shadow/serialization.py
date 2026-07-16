from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping


FORBIDDEN_KEYS = {
    "api_key", "authorization", "authorization_header", "credential", "credentials",
    "raw_provider_request", "raw_provider_response", "source_text", "translation_text",
    "prompt", "provider_request", "provider_response",
}


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def validate_safe_metadata(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).strip().lower() in FORBIDDEN_KEYS:
                raise ValueError(f"forbidden shadow metadata field: {key}")
            validate_safe_metadata(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            validate_safe_metadata(item)


def canonical_json(value: Any) -> str:
    validate_safe_metadata(_plain(value))
    return json.dumps(_plain(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def deterministic_fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def round_trip(value: Any) -> Any:
    return json.loads(canonical_json(value))
