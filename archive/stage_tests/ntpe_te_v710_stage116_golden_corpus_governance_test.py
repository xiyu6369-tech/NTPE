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
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage116_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v710_stage116_golden_corpus_governance_test.py", "--basetemp", str(sandbox)], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert int(result.stdout.split(" passed")[0].split()[-1]) >= 55, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage116_root", ignore_errors=True)
    artifact = json.loads((ROOT / "artifacts/te_v71_stage116/TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json").read_text(encoding="utf-8"))
    assert artifact["current_corpus_summary"]["approved_cases"] == 0
    assert artifact["boundary"]["stage117_started"] is False
    manifest = json.loads((ROOT / "manifests/te_v710_stage116_golden_corpus_governance_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    print("TE v7.1 Stage 11.6 Golden Corpus Governance ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
