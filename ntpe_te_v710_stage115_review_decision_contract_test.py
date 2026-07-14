from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage115_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v710_stage115_review_decision_contract_test.py", "--basetemp", str(sandbox)], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert int(result.stdout.split(" passed")[0].split()[-1]) >= 40, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage115_root", ignore_errors=True)
    artifact = json.loads((ROOT / "artifacts/te_v71_stage115/TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json").read_text(encoding="utf-8"))
    assert artifact["status"] == "completed" and artifact["boundary"]["decision_applied"] is False
    manifest = json.loads((ROOT / "manifests/te_v710_stage115_review_decision_contract_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert manifest["boundaries"]["stage116_started"] is False
    print("TE v7.1 Stage 11.5 Human Review Decision Contract ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
