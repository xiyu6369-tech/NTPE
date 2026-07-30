from __future__ import annotations

import json

from tools.generate_te_v720_stage1258a_candidate_structural_failure_sealing import build_artifacts


def test_stage1258a_root_acceptance() -> None:
    artifacts = {path.name: json.loads(data) for path, data in build_artifacts().items()}
    summary = artifacts["sealing_summary.json"]
    assert summary["status"] == "PASS"
    assert summary["canary_status"] == "candidate_structural_failed"
    assert summary["provider_requests_added"] == 0
    assert summary["claim_hash_unchanged"] is True
    assert summary["response_hash_unchanged"] is True


if __name__ == "__main__":
    test_stage1258a_root_acceptance()
    print("TE_V720_STAGE1258A_ROOT_ACCEPTANCE=PASS")
