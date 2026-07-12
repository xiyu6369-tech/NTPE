from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from core.adaptive_context_profile_budget import (
    PROFILE_BUDGET_VERSION,
    PROFILE_CONTEXT_CAPS,
    ProfileBudgetRequest,
    evaluate_profile_budget,
)

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert PROFILE_BUDGET_VERSION == "7.0.0-stage08.2"
    assert PROFILE_CONTEXT_CAPS == {
        "fast": 64,
        "balanced": 96,
        "novel": 160,
        "literary": 192,
        "quality": 224,
        "premium": 256,
    }
    for profile, expected in PROFILE_CONTEXT_CAPS.items():
        decision = evaluate_profile_budget(ProfileBudgetRequest(profile, 8192, 512, 1024, 1024))
        assert decision.ready
        assert decision.effective_context_tokens == expected
        assert decision.metadata["runtime_auto_hook"] is False
        assert decision.metadata["content_redacted"] is True

    blocked = evaluate_profile_budget(ProfileBudgetRequest("unknown", 8192, 512, 1024, 1024))
    assert not blocked.ready and "profile-not-supported" in blocked.blockers
    zero = evaluate_profile_budget(ProfileBudgetRequest("literary", 1000, 500, 300, 200))
    assert not zero.ready and "no-context-capacity" in zero.blockers

    basetemp = ROOT / ".ntpe_pytest_basetemp_stage082"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v700_stage082_profile_aware_context_budget_test.py", "--basetemp", str(basetemp)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "2 passed" in result.stdout
    finally:
        shutil.rmtree(basetemp, ignore_errors=True)

    manifest = json.loads((ROOT / "manifests/te_v700_stage082_profile_aware_context_budget_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        if name.startswith("manifests/"):
            json.loads(path.read_text(encoding="utf-8"))
            continue
        if digest == "mutable-structured-artifact":
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload["version"] == PROFILE_BUDGET_VERSION
            assert payload["metadata"]["content_redacted"] is True
            assert payload["metadata"]["runtime_auto_hook"] is False
            continue
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name

    print("TE v7.0 Stage 08.2 Profile-aware Context Budget ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
