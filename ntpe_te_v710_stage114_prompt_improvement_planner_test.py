from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.translation_prompt_improvement_planner import verify_improvement_plan_artifact

ROOT = Path(__file__).resolve().parent


def main() -> int:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage114_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v710_stage114_prompt_improvement_planner_test.py", "--basetemp", str(sandbox)], cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert int(result.stdout.split(" passed")[0].split()[-1]) >= 30, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "stage114_root", ignore_errors=True)
    artifact = verify_improvement_plan_artifact(ROOT / "artifacts/te_v71_stage114/TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json")
    assert len(artifact["plans"]) == 6 and artifact["plans_applied"] == 0
    assert all(row["implementation_status"] == "planned_not_applied" and row["requires_human_approval"] for row in artifact["plans"])
    manifest = json.loads((ROOT / "manifests/te_v710_stage114_prompt_improvement_planner_manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert manifest["prompt_modified"] is False and manifest["plans_applied"] == 0
    print("TE v7.1 Stage 11.4 Prompt Improvement Planner ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
