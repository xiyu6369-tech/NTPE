from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_provider_execution_freeze import FREEZE_VERSION, verify_freeze_artifact

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert FREEZE_VERSION == "7.0.0-stage10.8"
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage108_root" / uuid.uuid4().hex
    result = subprocess.run([
        sys.executable, "-m", "pytest", "-q",
        "tests/integration/translation_engine_v700_stage108_fake_transport_end_to_end_freeze_test.py",
        "--basetemp", str(sandbox),
    ], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        passed = int(result.stdout.split(" passed")[0].split()[-1])
        assert passed >= 20, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage108_root", ignore_errors=True)
    manifest = json.loads((
        ROOT / "manifests/te_v700_stage108_fake_transport_end_to_end_freeze_manifest.json"
    ).read_text(encoding="utf-8"))
    assert manifest["stage"] == "TE-v7.0-Stage10.8"
    assert manifest["network_requests"] == 0
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    frozen = verify_freeze_artifact(
        ROOT / "artifacts/te_v7_stage108/TE_V7_STAGE108_FAKE_TRANSPORT_FREEZE.json"
    )
    assert frozen.network_requests == 0 and frozen.real_provider_executed is False
    print("TE v7.0 Stage 10.8 Fake-Transport End-to-End Freeze ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
