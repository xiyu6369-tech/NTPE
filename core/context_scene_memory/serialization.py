from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .store import ContextMemoryStore
from .validation import ContextSceneValidationError


def dumps_context_store(store: ContextMemoryStore, *, indent: int | None = None) -> str:
    return json.dumps(store.to_dict(), ensure_ascii=False, indent=indent, sort_keys=True) + ("\n" if indent is not None else "")


def loads_context_store(payload: str | bytes) -> ContextMemoryStore:
    try:
        data: Any = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ContextSceneValidationError("invalid context store JSON") from exc
    if not isinstance(data, Mapping):
        raise ContextSceneValidationError("context store JSON must be an object")
    return ContextMemoryStore.from_dict(data)


def save_context_store(path: str | Path, store: ContextMemoryStore) -> None:
    target = Path(path)
    target.write_text(dumps_context_store(store), encoding="utf-8", newline="\n")


def load_context_store(path: str | Path) -> ContextMemoryStore:
    return loads_context_store(Path(path).read_bytes())
