from __future__ import annotations
from collections import deque
from threading import RLock
from .model import CanaryRecord
_LOCK=RLock(); _RECORDS: deque[CanaryRecord]=deque(maxlen=256); _ACTIVATED:set[str]=set()
def append_canary_record(record:CanaryRecord)->None:
    with _LOCK:
        _RECORDS.append(record)
        if record.activated: _ACTIVATED.add(record.package_id)
def canary_records()->tuple[CanaryRecord,...]:
    with _LOCK: return tuple(_RECORDS)
def clear_canary_records()->None:
    with _LOCK: _RECORDS.clear(); _ACTIVATED.clear()
def already_activated()->bool:
    with _LOCK: return bool(_ACTIVATED)
