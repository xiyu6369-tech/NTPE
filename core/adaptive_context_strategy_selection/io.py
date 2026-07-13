from __future__ import annotations

import json
from pathlib import Path

from .model import StrategySelectionDecision, StrategySelectionEvidence


def load_strategy_selection_evidence(
    policy_report_path: str | Path,
    budget_report_path: str | Path,
) -> StrategySelectionEvidence:
    policy = json.loads(Path(policy_report_path).read_text(encoding="utf-8"))
    budget = json.loads(Path(budget_report_path).read_text(encoding="utf-8"))
    return StrategySelectionEvidence(
        policy_ready=bool(policy.get("ready", False)),
        policy_status=str(policy.get("status", "")),
        policy_mode=str(policy.get("mode", "")),
        policy_profile=str(policy.get("profile", "")).strip().lower(),
        rollout_percent=int(policy.get("rollout_percent", 0) or 0),
        budget_ready=bool(budget.get("ready", False)),
        budget_status=str(budget.get("status", "")),
        budget_profile=str(budget.get("profile", "")).strip().lower(),
        effective_context_tokens=int(budget.get("effective_context_tokens", 0) or 0),
        profile_cap_tokens=int(budget.get("profile_cap_tokens", 0) or 0),
        hard_limit_tokens=int(budget.get("hard_limit_tokens", 0) or 0),
    )


def write_strategy_selection_report(decision: StrategySelectionDecision, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
