from __future__ import annotations

from collections import deque
from threading import RLock

from .model import ShadowAuditRecord

_LOCK = RLock()
_RECORDS: deque[ShadowAuditRecord] = deque(maxlen=2048)


def append_shadow_record(record: ShadowAuditRecord) -> None:
    with _LOCK:
        _RECORDS.append(record)


def shadow_records() -> tuple[ShadowAuditRecord, ...]:
    with _LOCK:
        return tuple(_RECORDS)


def clear_shadow_records() -> None:
    with _LOCK:
        _RECORDS.clear()
