from __future__ import annotations
import hashlib, json
from collections.abc import Mapping

def canonical_hash(value: object) -> str:
    payload = json.dumps(_plain(value), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value
