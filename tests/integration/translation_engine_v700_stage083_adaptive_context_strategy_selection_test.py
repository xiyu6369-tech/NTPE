from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_strategy_selection import (
    SELECTED_STRATEGY,
    StrategySelectionEvidence,
    StrategySelectionRequest,
    evaluate_strategy_selection,
)

ROOT = Path(__file__).resolve().parents[2]


def _passing_evidence(profile: str = "literary") -> StrategySelectionEvidence:
    return StrategySelectionEvidence(
        policy_ready=True,
        policy_status="pass",
        policy_mode="production_canary",
        policy_profile=profile,
        rollout_percent=5,
        budget_ready=True,
        budget_status="pass",
        budget_profile=profile,
        effective_context_tokens=192 if profile == "literary" else 160,
        profile_cap_tokens=192 if profile == "literary" else 160,
        hard_limit_tokens=4096,
    )


def test_strategy_selection_pass_and_fail_closed() -> None:
    decision = evaluate_strategy_selection(
        _passing_evidence(),
        StrategySelectionRequest(profile="literary", explicitly_enabled=True),
    )
    assert decision.ready is True
    assert decision.strategy == SELECTED_STRATEGY
    assert decision.rollout_percent == 5
    assert decision.effective_context_tokens == 192
    assert decision.metadata["runtime_auto_hook"] is False

    killed = evaluate_strategy_selection(
        _passing_evidence(),
        StrategySelectionRequest(profile="literary", explicitly_enabled=True, kill_switch=True),
    )
    assert killed.ready is False
    assert killed.strategy == "disabled"
    assert "kill-switch-enabled" in killed.blockers

    mismatch = evaluate_strategy_selection(
        _passing_evidence("novel"),
        StrategySelectionRequest(profile="literary", explicitly_enabled=True),
    )
    assert mismatch.ready is False
    assert "profile-evidence-mismatch" in mismatch.blockers


def test_cli_strategy_selection_without_provider() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage083_strategy" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        policy = sandbox / "policy.json"
        budget = sandbox / "budget.json"
        report = sandbox / "strategy.json"
        policy.write_text(json.dumps({
            "version": "7.0.0-stage08.1",
            "status": "pass",
            "ready": True,
            "mode": "production_canary",
            "profile": "literary",
            "rollout_percent": 5,
        }), encoding="utf-8")
        budget.write_text(json.dumps({
            "version": "7.0.0-stage08.2",
            "status": "pass",
            "ready": True,
            "profile": "literary",
            "profile_cap_tokens": 192,
            "hard_limit_tokens": 4096,
            "effective_context_tokens": 192,
        }), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "launcher_translate.py",
                "regression",
                "--profile",
                "literary",
                "--ace-strategy-select-validate",
                "--ace-strategy-policy-report",
                str(policy),
                "--ace-strategy-budget-report",
                str(budget),
                "--ace-strategy-report",
                str(report),
                "--ace-strategy-enable",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        payload = json.loads(report.read_text(encoding="utf-8"))
        assert payload["ready"] is True
        assert payload["strategy"] == SELECTED_STRATEGY
        assert payload["metadata"]["automatic_runtime_activation"] is False
        assert "provider request" not in result.stdout.lower()
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
