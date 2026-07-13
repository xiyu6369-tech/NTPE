from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Mapping

from .model import ProductionEvidence

POLICY_VERSION = "7.0.0-stage08.1"
BUDGET_VERSION = "7.0.0-stage08.2"
STRATEGY_VERSION = "7.0.0-stage08.3"
SELECTED_STRATEGY = "safe_extractive_production_canary"
FORBIDDEN_KEYS = {"text", "source_text", "translation", "translated_text", "prompt", "previous_context", "api_key"}


def _load(path: str | Path) -> tuple[dict[str, object], Path]:
    target = Path(path)
    value = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"report must be an object: {target}")
    return value, target


def _contains_forbidden_key(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(str(key).strip().lower() in FORBIDDEN_KEYS or _contains_forbidden_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def load_production_evidence(
    policy_report: str | Path,
    budget_report: str | Path,
    strategy_report: str | Path,
    *,
    max_age_seconds: int = 604_800,
    now: float | None = None,
) -> ProductionEvidence:
    policy, policy_path = _load(policy_report)
    budget, budget_path = _load(budget_report)
    strategy, strategy_path = _load(strategy_report)
    blockers: list[str] = []
    current = time.time() if now is None else float(now)
    paths = (policy_path, budget_path, strategy_path)
    fresh = max_age_seconds > 0 and all(0 <= current - path.stat().st_mtime <= max_age_seconds for path in paths)
    if not fresh:
        blockers.append("stale-evidence")
    integrity = not any(_contains_forbidden_key(value) for value in (policy, budget, strategy))
    if not integrity:
        blockers.append("unsafe-evidence-payload")
    if str(policy.get("version", "")) != POLICY_VERSION:
        blockers.append("policy-version-mismatch")
    if str(budget.get("version", "")) != BUDGET_VERSION:
        blockers.append("budget-version-mismatch")
    if str(strategy.get("version", "")) != STRATEGY_VERSION:
        blockers.append("strategy-version-mismatch")

    def integer(data: Mapping[str, object], key: str) -> int:
        value = data.get(key)
        if isinstance(value, bool):
            raise ValueError(f"invalid integer field: {key}")
        return int(value)

    try:
        evidence = ProductionEvidence(
            policy_version=str(policy.get("version", "")),
            policy_ready=policy.get("ready") is True,
            policy_status=str(policy.get("status", "")),
            policy_mode=str(policy.get("mode", "")),
            policy_profile=str(policy.get("profile", "")).lower(),
            policy_rollout_percent=integer(policy, "rollout_percent"),
            budget_version=str(budget.get("version", "")),
            budget_ready=budget.get("ready") is True,
            budget_status=str(budget.get("status", "")),
            budget_profile=str(budget.get("profile", "")).lower(),
            effective_context_tokens=integer(budget, "effective_context_tokens"),
            strategy_version=str(strategy.get("version", "")),
            strategy_ready=strategy.get("ready") is True,
            strategy_status=str(strategy.get("status", "")),
            strategy=str(strategy.get("strategy", "")),
            strategy_profile=str(strategy.get("profile", "")).lower(),
            strategy_rollout_percent=integer(strategy, "rollout_percent"),
            strategy_context_tokens=integer(strategy, "effective_context_tokens"),
            evidence_fresh=fresh,
            evidence_integrity=integrity and not blockers,
            blockers=tuple(blockers),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"malformed production evidence: {exc}") from exc
    return evidence
