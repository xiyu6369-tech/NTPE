from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from core.adaptive_context_strategy_selection import (
    SELECTED_STRATEGY,
    STRATEGY_SELECTION_VERSION,
    StrategySelectionEvidence,
    StrategySelectionRequest,
    evaluate_strategy_selection,
)

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert STRATEGY_SELECTION_VERSION == "7.0.0-stage08.3"
    evidence = StrategySelectionEvidence(
        True, "pass", "production_canary", "literary", 5,
        True, "pass", "literary", 192, 192, 4096,
    )
    decision = evaluate_strategy_selection(
        evidence,
        StrategySelectionRequest("literary", explicitly_enabled=True),
    )
    assert decision.ready
    assert decision.strategy == SELECTED_STRATEGY
    assert decision.metadata["runtime_auto_hook"] is False
    assert decision.metadata["automatic_runtime_activation"] is False

    blocked = evaluate_strategy_selection(
        evidence,
        StrategySelectionRequest("literary", explicitly_enabled=False),
    )
    assert not blocked.ready
    assert "explicit-enable-required" in blocked.blockers

    basetemp = ROOT / ".ntpe_pytest_basetemp_stage083"
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q",
            "tests/integration/translation_engine_v700_stage083_adaptive_context_strategy_selection_test.py",
            "--basetemp", str(basetemp),
        ],
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

    manifest = json.loads((ROOT / "manifests/te_v700_stage083_adaptive_context_strategy_selection_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        if name.startswith("manifests/"):
            json.loads(path.read_text(encoding="utf-8"))
            continue
        if digest == "mutable-structured-artifact":
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload["version"] == STRATEGY_SELECTION_VERSION
            assert payload["metadata"]["content_redacted"] is True
            assert payload["metadata"]["runtime_auto_hook"] is False
            continue
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name

    print("TE v7.0 Stage 08.3 Adaptive Context Strategy Selection ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
