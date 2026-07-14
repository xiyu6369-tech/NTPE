from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_provider_evidence_pipeline import PIPELINE_VERSION

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert PIPELINE_VERSION == "7.0.0-stage10.7"
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage107_root" / uuid.uuid4().hex
    result = subprocess.run([
        sys.executable, "-m", "pytest", "-q",
        "tests/integration/translation_engine_v700_stage107_provider_evidence_artifact_pipeline_test.py",
        "--basetemp", str(sandbox),
    ], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        passed = int(result.stdout.split(" passed")[0].split()[-1])
        assert passed >= 20, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage107_root", ignore_errors=True)
    manifest = json.loads((
        ROOT / "manifests/te_v700_stage107_provider_evidence_artifact_pipeline_manifest.json"
    ).read_text(encoding="utf-8"))
    assert manifest["stage"] == "TE-v7.0-Stage10.7"
    assert manifest["network_requests"] == 0
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    print("TE v7.0 Stage 10.7 Provider Evidence Artifact Pipeline ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
