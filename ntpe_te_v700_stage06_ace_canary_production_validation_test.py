from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARTIFACT = "artifacts/te_v7_stage06/TE_V7_STAGE06_CANARY_PRODUCTION_VALIDATION.json"


def _validate_mutable_artifact(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("version") == "7.0.0-stage06"
    assert isinstance(data.get("status"), str) and data["status"]
    assert isinstance(data.get("ready"), bool)
    metadata = data.get("metadata", {})
    assert isinstance(metadata, dict)
    assert metadata.get("content_redacted") is True
    assert metadata.get("single_chunk_only") is True
    assert metadata.get("automatic_expansion") is False
    assert metadata.get("translation_quality_improvement_claimed") is False
    assert metadata.get("provider_latency_improvement_claimed") is False
    if "provider_calls_added" in data:
        assert data["provider_calls_added"] == 0
    if data.get("ready") is True:
        assert data.get("status") == "pass"
        assert data.get("activated_records") == 1
        assert data.get("payload_changed_records") == 1


def main() -> int:
    from core.adaptive_context_canary import clear_canary_records, apply_prompt_package_canary
    from core.adaptive_context_canary_validation import build_canary_production_report, canary_validation_session
    from core.adaptive_context_integration.utils import canonical_hash

    original = ("第一句完整保留。第二句也完整保留。第三句提供更多背景。" * 20)
    package = {
        "package_id": "stage06",
        "session": {"chunk_index": 2},
        "context": {"previous_chunk_tail": original},
        "prompt": {"user_prompt": "前文：\n" + original + "\n待翻譯"},
    }
    baseline = canonical_hash(package)
    env_keys = (
        "NTPE_TE_V7_ACE_MODE",
        "NTPE_TE_V7_ACE_CANARY_CHUNK",
        "NTPE_TE_V7_ACE_CANARY_CONTEXT_TOKENS",
        "NTPE_TE_V7_ACE_CANARY_AUDIT",
    )
    previous = {key: os.environ.get(key) for key in env_keys}
    with tempfile.TemporaryDirectory(dir=ROOT) as td:
        audit = str(Path(td) / "audit.jsonl")
        with canary_validation_session(target_chunk=2, context_tokens=24, audit_path=audit):
            record = apply_prompt_package_canary(package)
            assert record and record.attempted and record.activated
            assert canonical_hash(package) != baseline
            report = build_canary_production_report(
                {"status": "success"},
                target_chunk=2,
                provider_execution_requested=False,
                stage="test",
            )
            assert not report.ready and report.status == "pass_without_provider_activation"
            assert report.activated_records == 1 and report.payload_changed_records == 1
            assert report.provider_calls_added == 0 and report.estimated_tokens_saved > 0
            assert Path(audit).exists()
        for key, value in previous.items():
            assert os.environ.get(key) == value, key

    manifest = json.loads(
        (ROOT / "manifests/te_v700_stage06_ace_canary_production_validation_manifest.json").read_text(encoding="utf-8")
    )
    mutable = set(manifest.get("integrity", {}).get("mutable_artifacts", ()))
    assert ARTIFACT in mutable
    for name, digest in manifest["integrity"]["files"].items():
        assert name not in mutable
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    _validate_mutable_artifact(ROOT / ARTIFACT)

    print("TE v7.0 Stage 06 ACE Canary Production Validation ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
