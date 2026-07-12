from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    manifest_path = ROOT / "manifests/te_v700_stage071_manifest_chain_decoupling_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, digest in manifest["integrity"]["files"].items():
        target = ROOT / name
        assert target.exists(), name
        assert not name.startswith("manifests/"), name
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name

    import ntpe_te_v700_stage051_mutable_validation_artifact_integrity_fix_test as stage051
    import ntpe_te_v700_stage06_ace_canary_production_validation_test as stage06
    import ntpe_te_v700_stage061_canary_validation_test_hardening_test as stage061
    import ntpe_te_v700_stage07_ace_canary_resume_test as stage07

    assert stage051.main() == 0
    assert stage06.main() == 0
    assert stage061.main() == 0
    assert stage07.main() == 0
    print("TE v7.0 Stage 07.1 Manifest Chain Decoupling ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
