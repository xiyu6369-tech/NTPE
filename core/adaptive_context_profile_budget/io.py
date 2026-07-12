from __future__ import annotations

import json
from pathlib import Path

from .model import ProfileBudgetDecision


def write_profile_budget_report(decision: ProfileBudgetDecision, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
