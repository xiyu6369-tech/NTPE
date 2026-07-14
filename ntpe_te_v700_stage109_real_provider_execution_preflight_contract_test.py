from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_real_provider_preflight import (
    PREFLIGHT_VERSION,
    verify_preflight_artifact,
)

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert PREFLIGHT_VERSION == "7.0.0-stage10.9"
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage109_root" / uuid.uuid4().hex
    result = subprocess.run([
        sys.executable, "-m", "pytest", "-q",
        "tests/integration/translation_engine_v700_stage109_real_provider_execution_preflight_contract_test.py",
        "--basetemp", str(sandbox),
    ], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        passed = int(result.stdout.split(" passed")[0].split()[-1])
        assert passed >= 25, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage109_root", ignore_errors=True)
    manifest = json.loads((
        ROOT / "manifests/te_v700_stage109_real_provider_execution_preflight_contract_manifest.json"
    ).read_text(encoding="utf-8"))
    assert manifest["stage"] == "TE-v7.0-Stage10.9"
    assert manifest["network_requests"] == 0
    assert manifest["provider_executed"] is False
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    artifact = verify_preflight_artifact(
        ROOT / "artifacts/te_v7_stage109/TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT.json"
    )
    assert artifact.status == "eligible_for_explicit_real_provider_authorization"
    assert artifact.provider_executed is False and artifact.network_requests == 0
    print("TE v7.0 Stage 10.9 Real Provider Execution Preflight Contract ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
