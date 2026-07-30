from __future__ import annotations

import json

from tools.generate_te_v720_stage1258_candidate_structural_verification_canary import build_preparation_artifacts


def test_stage1258_root_acceptance() -> None:
    artifacts = {path.name: json.loads(data) for path, data in build_preparation_artifacts().items()}
    summary = artifacts["preparation_summary.json"]
    assert summary["status"] == "PASS"
    assert summary["provider_requests"] == 0 and summary["network_requests"] == 0
    assert summary["execution_claim_created"] is False


if __name__ == "__main__":
    test_stage1258_root_acceptance()
    print("TE_V720_STAGE1258_ROOT_ACCEPTANCE=PASS")
