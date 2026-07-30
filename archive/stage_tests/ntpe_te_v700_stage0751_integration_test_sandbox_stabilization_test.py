from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INTEGRATION_TEST = ROOT / "tests/integration/translation_engine_v700_stage075_canary_ab_quality_validation_test.py"


def main() -> int:
    text = INTEGRATION_TEST.read_text(encoding="utf-8")
    assert "tmp_path" not in text
    assert ".ntpe_test_sandbox" in text
    assert "shutil.rmtree" in text

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(INTEGRATION_TEST),
            "--basetemp",
            str(ROOT / ".ntpe_pytest_basetemp_stage0751"),
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
        import shutil
        shutil.rmtree(ROOT / ".ntpe_pytest_basetemp_stage0751", ignore_errors=True)

    manifest = json.loads(
        (ROOT / "manifests/te_v700_stage0751_integration_test_sandbox_stabilization_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        if name.startswith("manifests/"):
            json.loads(path.read_text(encoding="utf-8"))
            continue
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name

    print("TE v7.0 Stage 07.5.1 Integration Test Sandbox Stabilization ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
