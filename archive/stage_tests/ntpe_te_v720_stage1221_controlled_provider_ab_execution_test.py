from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage1221_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v720_stage1221_controlled_provider_ab_execution_test.py", "--basetemp", str(sandbox)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert int(result.stdout.split(" passed")[0].split()[-1]) >= 50, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage1221_root", ignore_errors=True)

    manifest = json.loads((ROOT / "manifests/te_v720_stage1221_controlled_provider_ab_execution_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert _sha(ROOT / name) == digest, name
    for name, digest in manifest["compatibility_anchors"].items():
        assert _sha(ROOT / name) == digest, name

    execution = json.loads((ROOT / "artifacts/te_v72_stage1221/TE_V72_STAGE1221_CONTROLLED_AB_EXECUTION.json").read_text(encoding="utf-8"))
    assert execution["network_requests"] == 1 and execution["retry_count"] == 0
    assert execution["baseline_requests"] == 1 and execution["candidate_requests"] == 0
    assert execution["status"] == "ab_pair_incomplete" and execution["fallback_used"] is False
    print("TE v7.2 Stage 12.2.1 Controlled Provider A/B Execution ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
