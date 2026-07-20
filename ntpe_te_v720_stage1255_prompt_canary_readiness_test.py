from __future__ import annotations

import json

from tools.generate_te_v720_stage1255_prompt_canary_readiness import ARTIFACT_ROOT, build_artifacts


def test_stage1255_root_acceptance() -> None:
    expected = build_artifacts()
    assert set(expected) == {path.name for path in ARTIFACT_ROOT.iterdir() if path.is_file()}
    assert all((ARTIFACT_ROOT / name).read_bytes() == value for name, value in expected.items())
    payloads = {name: json.loads(value) for name, value in expected.items()}
    assert payloads["prompt_layout.json"]["status"] == "PASS"
    assert payloads["marker_integrity.json"]["status"] == "PASS"
    assert payloads["reference_isolation.json"]["status"] == "PASS"
    assert payloads["prompt_fingerprint.json"]["values_equal"] is True
    summary = payloads["readiness_summary.json"]
    assert summary["prompt_canary_ready"] is True
    assert summary["provider_eligible"] is False
    assert summary["provider_requests_added"] == summary["network_requests_added"] == summary["retry_added"] == 0
    assert summary["fallback"] is False


def main() -> int:
    test_stage1255_root_acceptance()
    print("TE_V720_STAGE1255_ROOT_ACCEPTANCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
