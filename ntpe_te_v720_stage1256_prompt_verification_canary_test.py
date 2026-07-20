from __future__ import annotations
from tools.generate_te_v720_stage1256_prompt_verification_canary import build_offline_preflight_artifacts

def test_stage1256_root_acceptance() -> None:
    result = build_offline_preflight_artifacts()
    assert result["request_count"] == 0
    assert result["status"] == "preflight_failure_no_provider_request"

if __name__ == "__main__":
    test_stage1256_root_acceptance(); print("TE_V720_STAGE1256_ROOT_ACCEPTANCE=PASS")
