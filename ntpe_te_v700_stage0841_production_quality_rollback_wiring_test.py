from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_production_rollout import OUTCOME_VERSION, ProductionOutcome

ROOT = Path(__file__).resolve().parent


def main() -> int:
    contract = ProductionOutcome()
    assert OUTCOME_VERSION == "7.0.0-stage08.4.1"
    assert contract.to_dict()["content_redacted"] is True
    basetemp = ROOT / ".ntpe_test_sandbox" / "stage0841_root" / uuid.uuid4().hex
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v700_stage0841_production_quality_rollback_wiring_test.py", "--basetemp", str(basetemp)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "7 passed" in result.stdout
    finally:
        shutil.rmtree(basetemp.parent.parent, ignore_errors=True)
    manifest = json.loads((ROOT / "manifests/te_v700_stage0841_production_quality_rollback_wiring_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "TE-v7.0-Stage08.4.1"
    assert manifest["nested_manifest_sha256_chain"] is False
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        if digest in {"mutable-structured-artifact", "self-describing-manifest"}:
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8"))
            continue
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    print("TE v7.0 Stage 08.4.1 Production Quality Rollback Wiring ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
