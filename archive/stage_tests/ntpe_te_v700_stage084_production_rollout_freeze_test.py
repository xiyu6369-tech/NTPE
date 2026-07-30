from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from core.adaptive_context_production_rollout import (
    FREEZE_VERSION,
    MAX_ROLLOUT_PERCENT,
    STAGE08_FREEZE_CONTRACT,
    validate_freeze_contract,
)

ROOT = Path(__file__).resolve().parent


def main() -> int:
    assert FREEZE_VERSION == "7.0.0-stage08.4"
    assert MAX_ROLLOUT_PERCENT == 5
    assert validate_freeze_contract() == ()
    assert STAGE08_FREEZE_CONTRACT["provider_calls_added"] == 0
    assert STAGE08_FREEZE_CONTRACT["te_v6_backward_compatible"] is True
    assert STAGE08_FREEZE_CONTRACT["te_v7_final_release"] is False

    basetemp = ROOT / ".ntpe_test_sandbox" / "stage084_root" / uuid.uuid4().hex
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/integration/translation_engine_v700_stage084_production_rollout_test.py", "--basetemp", str(basetemp)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "11 passed" in result.stdout
    finally:
        shutil.rmtree(basetemp.parent.parent, ignore_errors=True)

    manifest = json.loads((ROOT / "manifests/te_v700_stage084_production_rollout_freeze_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "TE-v7.0-Stage08.4"
    assert manifest["nested_manifest_sha256_chain"] is False
    for name, digest in manifest["files"].items():
        path = ROOT / name
        assert path.exists(), name
        if digest == "mutable-structured-artifact":
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload["version"] == FREEZE_VERSION
            assert payload["content_redacted"] is True
            continue
        if digest == "self-describing-manifest":
            json.loads(path.read_text(encoding="utf-8"))
            continue
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    for prior in ROOT.glob("manifests/te_v700_stage0*.json"):
        if prior.name.startswith("te_v700_stage084"):
            continue
        data = json.loads(prior.read_text(encoding="utf-8"))
        pinned = data.get("files", data.get("integrity", {}).get("files", {}))
        assert "ntpe_production_translate.py" not in pinned, prior.name
    print("TE v7.0 Stage 08.4 Production Rollout Freeze ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
