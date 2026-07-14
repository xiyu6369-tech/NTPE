from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.translation_quality_review_artifacts import verify_review_artifact

ROOT = Path(__file__).resolve().parent


def main() -> int:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage113_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v710_stage113_review_artifact_system_test.py", "--basetemp", str(sandbox)], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert int(result.stdout.split(" passed")[0].split()[-1]) >= 30, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage113_root", ignore_errors=True)
    names = ("REVIEW", "REVIEW_SUMMARY", "REVIEW_METRICS", "REVIEW_DEFECTS")
    payloads = [verify_review_artifact(ROOT / f"artifacts/te_v71_stage113/TE_V71_STAGE113_{name}.json") for name in names]
    assert all(row["stage"] == "TE-v7.1-Stage11.3" for row in payloads)
    manifest = json.loads((ROOT / "manifests/te_v710_stage113_review_artifact_system_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert manifest["content_redacted"] is True
    print("TE v7.1 Stage 11.3 Review Artifact System ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
