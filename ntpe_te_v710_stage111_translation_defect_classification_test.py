from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.translation_quality_corpus import load_golden_corpus
from core.translation_quality_defects import verify_defect_artifact

ROOT = Path(__file__).resolve().parent


def main() -> int:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage111_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v710_stage111_translation_defect_classification_test.py", "--basetemp", str(sandbox)], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert int(result.stdout.split(" passed")[0].split()[-1]) >= 30, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage111_root", ignore_errors=True)
    artifact = verify_defect_artifact(ROOT / "artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json")
    assert artifact["defect_count"] == 6 and artifact["blocking_defect_count"] == 1
    assert len(load_golden_corpus(ROOT / "quality_corpus/golden_review/te_v71_initial_defects.json")) == 6
    manifest = json.loads((ROOT / "manifests/te_v710_stage111_translation_defect_classification_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert manifest["network_requests"] == 0 and manifest["new_translation_generated"] is False
    print("TE v7.1 Stage 11.1 Translation Defect Classification ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
