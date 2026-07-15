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
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage122_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v720_stage122_controlled_provider_ab_validation_test.py", "--basetemp", str(sandbox)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert int(result.stdout.split(" passed")[0].split()[-1]) >= 50, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage122_root", ignore_errors=True)

    manifest = json.loads((ROOT / "manifests/te_v720_stage122_controlled_provider_ab_validation_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert _sha(ROOT / name) == digest, name
    for name, digest in manifest["compatibility_anchors"].items():
        assert _sha(ROOT / name) == digest, name

    package = json.loads((ROOT / "artifacts/te_v72_stage122/TE_V72_STAGE122_AB_EXECUTION_PACKAGE.json").read_text(encoding="utf-8"))
    boundary = package["boundary"]
    assert boundary["provider_executed"] is False and boundary["comparison_executed"] is False
    assert boundary["new_translation_generated"] is False and boundary["candidate_modified"] is False
    assert boundary["runtime_modified"] is False and boundary["provider_modified"] is False
    assert boundary["prompt_modified"] is False and boundary["stage123_started"] is False
    print("TE v7.2 Stage 12.2 Controlled Provider A/B Quality Validation ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
