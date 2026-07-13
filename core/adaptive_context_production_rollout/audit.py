from __future__ import annotations

import json
from pathlib import Path

from .model import RolloutRecord


def write_rollout_audit(record: RolloutRecord, path: str | Path | None) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
