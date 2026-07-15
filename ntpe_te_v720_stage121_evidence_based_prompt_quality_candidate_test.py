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
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage121_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v720_stage121_evidence_based_prompt_quality_candidate_test.py", "--basetemp", str(sandbox)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert int(result.stdout.split(" passed")[0].split()[-1]) >= 30, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage121_root", ignore_errors=True)

    manifest = json.loads((ROOT / "manifests/te_v720_stage121_evidence_based_prompt_quality_candidate_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert _sha(ROOT / name) == digest, name
    for name, digest in manifest["compatibility_anchors"].items():
        assert _sha(ROOT / name) == digest, name

    boundary = json.loads((ROOT / "artifacts/te_v72_stage121/TE_V72_STAGE121_EVIDENCE_BASED_PROMPT_QUALITY_CANDIDATE.json").read_text(encoding="utf-8"))["boundary"]
    assert boundary["network_requests"] == 0 and boundary["real_provider_executed"] is False
    assert boundary["stage11_framework_modified"] is False and boundary["golden_corpus_modified"] is False
    assert boundary["te_v72_stage122_started"] is False
    print("TE v7.2 Stage 12.1 Evidence-Based Prompt Quality Candidate ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
