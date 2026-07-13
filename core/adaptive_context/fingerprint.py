from __future__ import annotations

import hashlib
import json

from .model import SelectedContext


def context_fingerprint(selected: tuple[SelectedContext, ...] | list[SelectedContext]) -> str:
    payload = [{"id": row.item_id, "kind": row.kind, "content_sha256": hashlib.sha256(row.content.encode("utf-8")).hexdigest()} for row in selected]
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
