from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_single_real_invocation import (
    INVOCATION_VERSION,
    verify_invocation_artifact,
)

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert INVOCATION_VERSION == "7.0.0-stage10.10A"
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage1010_root" / uuid.uuid4().hex
    result = subprocess.run([
        sys.executable, "-m", "pytest", "-q",
        "tests/integration/translation_engine_v700_stage1010_single_real_provider_invocation_test.py",
        "--basetemp", str(sandbox),
    ], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        passed = int(result.stdout.split(" passed")[0].split()[-1])
        assert passed >= 30, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage1010_root", ignore_errors=True)
    manifest = json.loads((
        ROOT / "manifests/te_v700_stage1010_single_real_provider_invocation_manifest.json"
    ).read_text(encoding="utf-8"))
    assert manifest["stage"] == "TE-v7.0-Stage10.10A"
    assert manifest["network_requests"] == 0
    assert manifest["real_provider_executed"] is False
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    artifact = verify_invocation_artifact(
        ROOT / "artifacts/te_v7_stage1010/TE_V7_STAGE1010_SINGLE_REAL_INVOCATION.json"
    )
    assert artifact.status == "stage1010a_fake_transport_validated"
    assert artifact.network_requests == 0 and artifact.real_provider_execution is False
    print("TE v7.0 Stage 10.10A Single Real Provider Invocation Package ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
