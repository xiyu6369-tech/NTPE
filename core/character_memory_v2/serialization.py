from __future__ import annotations

import json
from typing import Any, Mapping

from .store import MemoryStore
from .validation import CharacterMemoryValidationError, validate_memory_store


def serialize_memory_store(store: MemoryStore) -> str:
    report = validate_memory_store(store)
    if not report["valid"]:
        raise CharacterMemoryValidationError("; ".join(report["errors"]))
    return json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def deserialize_memory_store(payload: str | bytes) -> MemoryStore:
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CharacterMemoryValidationError("serialized store must be UTF-8") from exc
    if not isinstance(payload, str):
        raise CharacterMemoryValidationError("serialized store must be text or bytes")
    try:
        data: Any = json.loads(payload)
    except (json.JSONDecodeError, TypeError) as exc:
        raise CharacterMemoryValidationError("malformed character memory JSON") from exc
    if not isinstance(data, Mapping):
        raise CharacterMemoryValidationError("serialized store root must be an object")
    try:
        return MemoryStore.from_dict(data)
    except CharacterMemoryValidationError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise CharacterMemoryValidationError("invalid character memory store payload") from exc
