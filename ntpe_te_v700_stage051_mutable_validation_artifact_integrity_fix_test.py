from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests/te_v700_stage051_mutable_validation_artifact_integrity_fix_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, digest in manifest["integrity"]["files"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    stage04 = json.loads((root / "manifests/te_v700_stage04_production_shadow_validation_manifest.json").read_text(encoding="utf-8"))
    mutable = stage04.get("mutable_artifacts", [])
    assert len(mutable) == 1
    path = mutable[0]["path"]
    assert path not in stage04["integrity"]["files"]
    assert path in stage04["inventory"]
    payload = json.loads((root / path).read_text(encoding="utf-8"))
    assert payload["version"] == "7.0.0-stage04"
    if "provider_calls_added" in payload:
        assert payload["provider_calls_added"] == 0
        assert payload["metadata"]["content_redacted"] is True
    else:
        assert payload["provider_execution_observed"] is False
        assert payload["translation_quality_improvement_claimed"] is False
    print("TE v7.0 Stage 05.1 Mutable Validation Artifact Integrity Fix ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
