from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from core.adaptive_context_activation_policy import (
    ActivationEvidence,
    ActivationPolicyRequest,
    MAX_STAGE081_ROLLOUT_PERCENT,
    POLICY_VERSION,
    evaluate_activation_policy,
)

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert POLICY_VERSION == "7.0.0-stage08.1"
    assert MAX_STAGE081_ROLLOUT_PERCENT == 5
    evidence = ActivationEvidence(True, "pass", "pass", 1, 99, 0, True)
    passed = evaluate_activation_policy(evidence, ActivationPolicyRequest("literary", 5, True, False))
    assert passed.ready and passed.mode == "production_canary"
    assert passed.metadata["automatic_activation"] is False
    assert passed.metadata["runtime_auto_hook"] is False
    assert passed.metadata["content_redacted"] is True

    for request, expected in (
        (ActivationPolicyRequest("literary", 5, False, False), "explicit-enable-required"),
        (ActivationPolicyRequest("literary", 6, True, False), "rollout-percent-exceeds-stage-limit"),
        (ActivationPolicyRequest("fast", 5, True, False), "profile-not-allowed"),
        (ActivationPolicyRequest("literary", 5, True, True), "kill-switch-enabled"),
    ):
        decision = evaluate_activation_policy(evidence, request)
        assert not decision.ready
        assert expected in decision.blockers
        assert decision.mode == "disabled"

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v700_stage081_production_activation_policy_test.py", "--basetemp", str(ROOT / ".ntpe_pytest_basetemp_stage081")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "2 passed" in result.stdout
    finally:
        import shutil
        shutil.rmtree(ROOT / ".ntpe_pytest_basetemp_stage081", ignore_errors=True)

    manifest = json.loads((ROOT / "manifests/te_v700_stage081_production_activation_policy_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        if name.startswith("manifests/"):
            json.loads(path.read_text(encoding="utf-8"))
            continue
        if digest == "mutable-structured-artifact":
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload["version"] == "7.0.0-stage08.1"
            assert payload["metadata"]["content_redacted"] is True
            assert payload["metadata"]["runtime_auto_hook"] is False
            continue
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name

    print("TE v7.0 Stage 08.1 Production Activation Policy ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
