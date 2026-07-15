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
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage1223_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v720_stage1223_minimal_excerpt_ab_quality_validation_test.py", "--basetemp", str(sandbox)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert int(result.stdout.split(" passed")[0].split()[-1]) >= 65, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage1223_root", ignore_errors=True)

    manifest = json.loads((ROOT / "manifests/te_v720_stage1223_minimal_excerpt_ab_quality_validation_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert _sha(ROOT / name) == digest, name
    for name, digest in manifest["compatibility_anchors"].items():
        assert _sha(ROOT / name) == digest, name

    execution = json.loads((ROOT / "artifacts/te_v72_stage1223/TE_V72_STAGE1223_MINIMAL_EXCERPT_AB_EXECUTION.json").read_text(encoding="utf-8"))
    assert execution["network_requests"] == 2
    assert execution["baseline_requests"] == 1 and execution["candidate_requests"] == 1
    assert execution["retry_count"] == 0 and execution["fallback_used"] is False
    assert execution["status"] == "ab_pair_partial" and execution["review_status"] == "not_reviewable_pair_incomplete"
    print("TE v7.2 Stage 12.2.3 Minimal-Excerpt Provider A/B Quality Validation ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
