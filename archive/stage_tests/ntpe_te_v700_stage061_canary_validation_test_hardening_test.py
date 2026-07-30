from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    manifest_path = ROOT / "manifests/te_v700_stage061_canary_validation_test_hardening_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, digest in manifest["integrity"]["files"].items():
        target = ROOT / name
        assert target.exists(), name
        if name.startswith("manifests/"):
            json.loads(target.read_text(encoding="utf-8"))
            continue
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name

    import ntpe_te_v700_stage06_ace_canary_production_validation_test as stage06

    assert stage06.main() == 0
    print("TE v7.0 Stage 06.1 Canary Validation Test Hardening ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
