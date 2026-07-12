from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_profile_budget import ProfileBudgetRequest, evaluate_profile_budget

ROOT = Path(__file__).resolve().parents[2]


def test_profile_caps_and_hard_limit_clamps() -> None:
    literary = evaluate_profile_budget(ProfileBudgetRequest("literary", 8192, 512, 1024, 1024))
    fast = evaluate_profile_budget(ProfileBudgetRequest("fast", 8192, 512, 1024, 1024))
    assert literary.ready and fast.ready
    assert literary.effective_context_tokens == 192
    assert fast.effective_context_tokens == 64
    assert literary.effective_context_tokens > fast.effective_context_tokens

    clamped = evaluate_profile_budget(ProfileBudgetRequest("premium", 1200, 400, 400, 300, 999))
    assert clamped.ready
    assert clamped.hard_limit_tokens == 100
    assert clamped.effective_context_tokens == 100
    assert "requested-budget-clamped-to-profile-cap" in clamped.limitations
    assert "profile-cap-clamped-to-hard-limit" in clamped.limitations


def test_cli_profile_budget_validation_without_provider() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage082_profile_budget" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        report = sandbox / "budget.json"
        result = subprocess.run(
            [
                sys.executable,
                "launcher_translate.py",
                "regression",
                "--profile",
                "literary",
                "--ace-profile-budget-validate",
                "--ace-profile-budget-report",
                str(report),
                "--ace-profile-budget-requested-tokens",
                "500",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        payload = json.loads(report.read_text(encoding="utf-8"))
        assert payload["ready"] is True
        assert payload["effective_context_tokens"] == 192
        assert payload["metadata"]["runtime_auto_hook"] is False
        assert payload["metadata"]["content_redacted"] is True
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
