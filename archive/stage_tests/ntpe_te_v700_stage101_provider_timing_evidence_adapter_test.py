from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_provider_evidence import PROVIDER_EVIDENCE_VERSION

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert PROVIDER_EVIDENCE_VERSION == "7.0.0-stage10.1"
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage101_root" / uuid.uuid4().hex
    result = subprocess.run([
        sys.executable, "-m", "pytest", "-q",
        "tests/integration/translation_engine_v700_stage101_provider_timing_evidence_adapter_test.py",
        "--basetemp", str(sandbox),
    ], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "16 passed" in result.stdout, result.stdout
    finally:
        shutil.rmtree(sandbox.parent.parent, ignore_errors=True)
    manifest_path = ROOT / "manifests/te_v700_stage101_provider_timing_evidence_adapter_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["stage"] == "TE-v7.0-Stage10.1"
    assert manifest["nested_manifest_sha256_chain"] is False
    assert manifest["real_provider_execution"] == "not_executed_with_provider"
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    print("TE v7.0 Stage 10.1 Provider Timing Evidence Adapter ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
