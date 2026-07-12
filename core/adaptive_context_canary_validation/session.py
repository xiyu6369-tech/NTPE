from __future__ import annotations
import os
from contextlib import contextmanager
from collections.abc import Iterator
from core.adaptive_context_canary import clear_canary_records

_ENV_KEYS = (
    "NTPE_TE_V7_ACE_MODE",
    "NTPE_TE_V7_ACE_CANARY_CHUNK",
    "NTPE_TE_V7_ACE_CANARY_CONTEXT_TOKENS",
    "NTPE_TE_V7_ACE_CANARY_AUDIT",
    "NTPE_TE_V7_ACE_CANARY_STOP_AFTER_TARGET",
)

@contextmanager
def canary_validation_session(*, target_chunk: int, context_tokens: int, audit_path: str | None = None) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in _ENV_KEYS}
    clear_canary_records()
    os.environ["NTPE_TE_V7_ACE_MODE"] = "canary"
    os.environ["NTPE_TE_V7_ACE_CANARY_CHUNK"] = str(max(1, int(target_chunk)))
    os.environ["NTPE_TE_V7_ACE_CANARY_CONTEXT_TOKENS"] = str(max(1, int(context_tokens)))
    os.environ["NTPE_TE_V7_ACE_CANARY_STOP_AFTER_TARGET"] = "1"
    if audit_path:
        os.environ["NTPE_TE_V7_ACE_CANARY_AUDIT"] = str(audit_path)
    else:
        os.environ.pop("NTPE_TE_V7_ACE_CANARY_AUDIT", None)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
