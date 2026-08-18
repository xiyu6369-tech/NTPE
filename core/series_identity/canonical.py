from __future__ import annotations

import hashlib
import json
from typing import Any


def to_canonical_json(obj: dict[str, Any]) -> str:
    """
    Deterministic JSON serialization: sorted keys, no whitespace, UTF-8.
    """
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_sha256(data: str | bytes) -> str:
    """Compute SHA-256 hex digest."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_manifest_fingerprint(manifest_dict: dict[str, Any]) -> str:
    """
    Compute SHA-256 of canonical manifest payload (excluding manifest_fingerprint itself).
    """
    payload = {k: v for k, v in manifest_dict.items() if k != "manifest_fingerprint"}
    canonical = to_canonical_json(payload)
    return compute_sha256(canonical)


def compute_series_fingerprint(series_id: str, series_name: str, created_at: str, updated_at: str) -> str:
    """
    Compute fingerprint for SeriesIdentity (used in manifest payload).
    """
    payload = {
        "series_id": series_id,
        "series_name": series_name,
        "created_at": created_at,
        "updated_at": updated_at,
    }
    canonical = to_canonical_json(payload)
    return compute_sha256(canonical)