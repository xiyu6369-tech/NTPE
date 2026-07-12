from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_activation_policy import (
    ActivationEvidence,
    ActivationPolicyRequest,
    evaluate_activation_policy,
)

ROOT = Path(__file__).resolve().parents[2]


def _sandbox() -> Path:
    path = ROOT / ".ntpe_test_sandbox" / "stage081_activation_policy" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path


def test_policy_pass_and_fail_closed() -> None:
    evidence = ActivationEvidence(
        ab_ready=True,
        ab_status="pass",
        canary_status="pass",
        canary_activated_records=1,
        estimated_tokens_saved=99,
        provider_calls_added=0,
        target_chunk_completed=True,
    )
    decision = evaluate_activation_policy(
        evidence,
        ActivationPolicyRequest(profile="literary", rollout_percent=5, explicitly_enabled=True),
    )
    assert decision.ready is True
    assert decision.mode == "production_canary"
    assert decision.rollout_percent == 5

    blocked = evaluate_activation_policy(
        evidence,
        ActivationPolicyRequest(profile="literary", rollout_percent=5, explicitly_enabled=True, kill_switch=True),
    )
    assert blocked.ready is False
    assert blocked.mode == "disabled"
    assert "kill-switch-enabled" in blocked.blockers


def test_cli_policy_validation_without_provider() -> None:
    sandbox = _sandbox()
    try:
        ab = sandbox / "ab.json"
        canary = sandbox / "canary.json"
        report = sandbox / "decision.json"
        ab.write_text(json.dumps({"status": "pass", "ready": True}), encoding="utf-8")
        canary.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "activated_records": 1,
                    "estimated_tokens_saved": 99,
                    "provider_calls_added": 0,
                    "target_chunk_completed": True,
                    "fallback_reasons": [],
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                "launcher_translate.py",
                "regression",
                "--profile",
                "literary",
                "--ace-production-policy-validate",
                "--ace-production-policy-ab-report",
                str(ab),
                "--ace-production-policy-canary-report",
                str(canary),
                "--ace-production-policy-report",
                str(report),
                "--ace-production-rollout-percent",
                "5",
                "--ace-production-enable",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        payload = json.loads(report.read_text(encoding="utf-8"))
        assert payload["ready"] is True
        assert payload["mode"] == "production_canary"
        assert payload["metadata"]["runtime_auto_hook"] is False
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
