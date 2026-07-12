from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    manifest_path = ROOT / "manifests/te_v700_stage072_canary_diagnostics_target_stop_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, digest in manifest["integrity"]["files"].items():
        target = ROOT / name
        assert target.exists(), name
        assert not name.startswith("manifests/"), name
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name

    from core.adaptive_context_canary_validation.stop import (
        STOP_MARKER,
        is_target_complete_result,
        should_stop_before_chunk,
    )

    assert STOP_MARKER == "TE_V7_CANARY_TARGET_COMPLETE"
    assert is_target_complete_result({
        "status": "failed",
        "records": [{"error": "TE_V7_CANARY_TARGET_COMPLETE:target_chunk=2"}],
    })
    assert not is_target_complete_result({"status": "success", "records": []})

    import ntpe_te_v700_stage07_ace_canary_resume_test as stage07
    import ntpe_te_v700_stage071_manifest_chain_decoupling_test as stage071
    assert stage07.main() == 0
    assert stage071.main() == 0
    print("TE v7.0 Stage 07.2 Canary Diagnostics and Target Stop ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
