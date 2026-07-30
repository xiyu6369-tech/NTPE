from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.translation_quality_metrics import verify_quality_metrics_artifact

ROOT = Path(__file__).resolve().parent


def main() -> int:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage112_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v710_stage112_translation_quality_metrics_test.py", "--basetemp", str(sandbox)], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert int(result.stdout.split(" passed")[0].split()[-1]) >= 30, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage112_root", ignore_errors=True)
    metrics = verify_quality_metrics_artifact(ROOT / "artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json")
    summary = verify_quality_metrics_artifact(ROOT / "artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_SUMMARY.json")
    assert metrics["quality_pass"] is False and summary["overall_score"] <= 49
    manifest = json.loads((ROOT / "manifests/te_v710_stage112_translation_quality_metrics_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert manifest["provider_execution_performed"] is False
    print("TE v7.1 Stage 11.2 Translation Quality Metrics ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
