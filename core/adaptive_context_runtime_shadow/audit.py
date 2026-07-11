from __future__ import annotations

import json
import os
from pathlib import Path

from .model import ShadowAuditRecord

AUDIT_ENV = "NTPE_TE_V7_ACE_SHADOW_AUDIT"


def write_shadow_audit(record: ShadowAuditRecord, path: str | Path | None = None) -> Path | None:
    target = str(path or os.environ.get(AUDIT_ENV, "")).strip()
    if not target:
        return None
    output = Path(target)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    return output
