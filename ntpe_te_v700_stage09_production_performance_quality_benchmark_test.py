from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_production_benchmark import BENCHMARK_VERSION, PRODUCTION_ROLLOUT_MAX_PERCENT

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert BENCHMARK_VERSION == "7.0.0-stage09"
    assert PRODUCTION_ROLLOUT_MAX_PERCENT == 5
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage09_root" / uuid.uuid4().hex
    result = subprocess.run([
        sys.executable, "-m", "pytest", "-q",
        "tests/integration/translation_engine_v700_stage09_production_performance_quality_benchmark_test.py",
        "--basetemp", str(sandbox),
    ], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "12 passed" in result.stdout, result.stdout
    finally:
        shutil.rmtree(sandbox.parent.parent, ignore_errors=True)
    manifest = json.loads((ROOT / "manifests/te_v700_stage09_production_performance_quality_benchmark_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "TE-v7.0-Stage09"
    assert manifest["nested_manifest_sha256_chain"] is False
    assert manifest["real_provider_benchmark"] == "not_executed_with_provider"
    for name, marker in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        if marker == "mutable-structured-artifact":
            assert json.loads(path.read_text(encoding="utf-8"))["content_redacted"] is True
    assert "ntpe_production_translate.py" in manifest["legal_evolution_entrypoints"]
    print("TE v7.0 Stage 09 Production Performance & Quality Benchmark ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
